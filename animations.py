import numpy as np
import time

'''
    Gonna need a list of keyframes, each keyframe will have:
        - position
        - texture id (only if in that frame the texture is switched, None otherwise)
        - time at which the frame occurrs
    
    When the animation starts start is set to time.time(), then time.time()-start is the time
    passed
'''

class Animation:

    def __init__(self, frames=None, looping=False, textures=None):
        self.frames = []
        self.running = False # whether the animation is playing
        self.textures = textures
        self.looping = looping
        self.curr_frame = 0
        self.start_time = 0
        if frames is not None:
            self.set_frames(frames)
    
    def __parse_frame(self, frame: dict, prev=None, delay=0.0) -> dict:
        '''
            Takes an incomplete representation of a frame and returns its parsed (complete)
            version, the missing values are taken from the previous frame prev if it's not None,
            the time is set to the previous frame's time plus the passed value for delay
        '''
        if not isinstance(frame['pos'], np.ndarray):
            frame['pos'] = np.array(frame['pos'])
        if 'time' not in frame:
            prev_time = 0
            if prev is not None and 'time' in prev:
                prev_time = prev['time']
            frame['time'] = prev_time + delay
        elif 'tex_idx' not in frame:
            prev_tex = None
            if prev is not None and 'tex_idx' in prev:
                prev_tex = prev['tex_idx']
            frame['tex_idx'] = prev_tex
        return frame

    def set_frames(self, frames=[], delay=0.2):
        '''
            Sets the frames to frames, each frame should be a dictionary with the following values:\n
            pos (x,y) -> the position of the object in the key frame \n
            time -> the amount of time from the start of the animation to the frame\n
            texture_id -> the texture id that the object takes from this time step to the next one
        '''
        if len(frames) == 0:
            self.frames = []
            return
        # INPUT PARSING
        frames[0] = self.__parse_frame(frames[0])
        for i in range(1, len(frames)):
            frames[i] = self.__parse_frame(frames[i], prev=frames[i-1], delay=delay)
        
        self.frames = frames

    def add_frame(self, frame: dict) -> None:
        self.frames.append(frame)

    def next_frame(self) -> None:
        '''
            Passes to the next frame
        '''
        self.curr_frame += 1
        if self.curr_frame == len(self.frames)-1: # if the animation finished
            self.curr_frame = 0 if self.looping else self.curr_frame
            self.running = self.looping

    def start(self, restart=True) -> None:
        if restart:
            self.curr_frame = 0
        self.running = True
        self.start_time = time.time()
        
    def stop(self):
        self.running = False

    def update(self) -> None:
        if not self.running:
            return

        if self.get_curr_play_time() >= self.frames[min(len(self.frames)-1, self.curr_frame+1)]['time']:
            self.next_frame()

    def get_curr_play_time(self) -> float:
        '''
            Returns the amount of time passed from the moment the animation was last started
        '''
        return time.time()-self.start_time

    def get_texture(self):
        '''
            Returns the texture of the current frame, None if it has no texture
        '''
        return None if self.textures is None else self.textures[self.frames[self.curr_frame]['tex_idx']]

    def update_frame(self) -> None:
        if not self.running:
            return
        prev_time, next_time = self.frames[self.curr_frame]['time'], self.frames[self.curr_frame+1]['time']
        if prev_time < self.get_curr_play_time() < next_time: # if we're in the right frame do nothing
            return
        # loop through every frame until you find one that hasn't yet been reached
        while self.frames[self.curr_frame+1]['time'] < self.get_curr_play_time():
            self.next_frame()
            if not self.running:
                break

    def get_pos(self, updating=False) -> tuple:
        '''
            Returns the position at the current frame, if one regularly calls anim.update() then
            setting updating=True will improve the performance of the method
        '''
        self.update_frame()
        if not self.running:
            return self.frames[self.curr_frame]['pos']

        # starting and ending positions
        xi, xf = self.frames[self.curr_frame]['pos'], self.frames[self.curr_frame+1]['pos']
        # starting and ending time
        ti, tf = self.frames[self.curr_frame]['time'], self.frames[self.curr_frame+1]['time'] 
        since_cframe_start = self.get_curr_play_time()-ti # time passed since the current frame started
        return xi+since_cframe_start/(tf-ti)*(xf-xi)
