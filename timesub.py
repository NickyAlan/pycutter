import math
import numpy as np
from cutter import CutterIt

class Timesub :
    '''
    - Input: .mp4 or mp3 file
    - Task: get time subtitle for video or audio file, easier for making subtitle

    Return :
        .srt file
    '''
    def __init__(self, filepath: str) :
        self.filepath = filepath
        self.cut = CutterIt(filepath=filepath)
        self.array = self.cut.array
        self.rate = self.cut.rate

    def sec2rate(self, sec: int) :
        '''convert second to sample rate'''
        return round(sec*self.rate)

    def rate2sec(self, samplerate: int) :
        '''convert sample rate to second'''
        return round(samplerate / self.rate , 3)

    def get_undercuts(self, array: np.array, cut_duration_sec=0.7, alpha=85) :   
        '''
        get list of under threshold value array (silence) in sample rate 
        '''     
        under_ts_rate = 0
        is_start_rate = True
        threshold = np.percentile(array[array > 0], q=alpha)
        duration_rate = array.shape[0]
        cut_duration_rate = self.sec2rate(cut_duration_sec)

        under_cuts = {}
        for rate_count, value in enumerate(array) :
            if value < threshold :
                under_ts_rate += 1
                if is_start_rate : 
                    start_cut = rate_count
                    is_start_rate = False
                if under_ts_rate >= cut_duration_rate :
                    under_cuts[start_cut] = rate_count 
            else :
                # reset every thing
                is_start_rate = True
                under_ts_rate = 0
        
        return list(under_cuts.items()), duration_rate
    
    def get_keeps_rate(self, under_cuts: list, duration_rate: int) :
        '''
        reversed undercuts list to speech part
        '''
        keeps_rate = []
        # undercuts = [(0,720), (900, 1002) ...] -> keeps_rate = [(0,0), (720, 900) ...] -> [(720: 900), ...] 
        previous_rate = 0 
        for start_rate, stop_rate in under_cuts :
            keeps_rate.append((previous_rate, start_rate))
            previous_rate = stop_rate
        
        # [(0, 0), (76374, 1181915) .. ] -> [(76374, 1181915) ... ]
        if keeps_rate : 
            if keeps_rate[0] == (0, 0) : keeps_rate = keeps_rate[1:]

            # forgot last speech part
            last_under_cuts_rate = under_cuts[-1][-1]
            if last_under_cuts_rate != duration_rate :
                keeps_rate.append((last_under_cuts_rate, duration_rate))

        return keeps_rate
    
    def get_keeps_rate_longer_than(self, keeps_rate: list, limit_speech_sec = 7) :
        ''' 
        seperate if speech part is longer than limit_speech_sec
        '''
        limit_speech_rate = self.sec2rate(limit_speech_sec)
        not_longer_part = []
        long_speech_part = []
        long_speech_part_start_rate = []
        for start_rate, stop_rate in keeps_rate :
            if (stop_rate - start_rate) > limit_speech_rate :
                long_speech_part.append(self.array[start_rate: stop_rate])
                long_speech_part_start_rate.append(start_rate)
            else :
                not_longer_part.append((start_rate, stop_rate))

        return long_speech_part, not_longer_part, long_speech_part_start_rate
    
    def add_start_rate(self, keep_rate: list, start_rate: int) :
        ''' 
        add start rate for the same rate with main array
        '''
        added_keep_rate = []
        for start, stop in keep_rate :
            start += start_rate
            stop += start_rate
            added_keep_rate.append((start, stop))

        return added_keep_rate
    
    def get_timesub(self) :
        '''
        Return timesubtitle list
        '''
        limit_sec=5
        undercuts, duration_rate = self.get_undercuts(self.array)
        keeps_rate = self.get_keeps_rate(undercuts, duration_rate)
        long_speechs, not_long_speechs, long_speech_rates = self.get_keeps_rate_longer_than(keeps_rate, limit_speech_sec=limit_sec)

        still_longer_speech = True
        cut_duration_sec = 0.25
        
        while still_longer_speech :
            # seperate speech_part longer than limit_speech_sec 
            speech_part = []
            for part, start_rate in zip(long_speechs, long_speech_rates) :
                undercut, duration_rate = self.get_undercuts(part, cut_duration_sec)
                keep_rate = self.get_keeps_rate(undercut, duration_rate)
                keep_rate = self.add_start_rate(keep_rate, start_rate)
                speech_part.append(keep_rate)
                
            # check if seperated part is still longer than limit_speech_sec: for next loop
            long_speechs = []
            long_speech_rates = []
            for seperated_part in speech_part :
                long_speech, not_long_speech, long_speech_rate = self.get_keeps_rate_longer_than(seperated_part)
                if long_speech_rate : # if still longer
                    long_speechs += long_speech
                    long_speech_rates += long_speech_rate
                # add not_long_speech
                not_long_speechs += not_long_speech

            if not long_speech_rates: still_longer_speech = False

        keeps_rate_sub = sorted(not_long_speechs, key=lambda x: x[0])
        # because previous will seperate each part very a few sec -> combined longer but less than 5 sec
        limit_rate = self.sec2rate(limit_sec)
        keeps_rate_long = []
        keeps_rate_ok = []
        for start_rate, stop_rate in keeps_rate :
            if (stop_rate - start_rate) > limit_rate :
                keeps_rate_long.append((start_rate, stop_rate))
            else :
                keeps_rate_ok.append((start_rate, stop_rate))

        long_idx = 0
        combine_list = []
        is_start = True
        for idx, (start_rate, stop_rate) in enumerate(keeps_rate_sub) :  
            # find start_rate
            if long_idx < len(keeps_rate_long) :
                if is_start :  
                    if start_rate == keeps_rate_long[long_idx][0] :
                        start_idx = idx
                        is_start = False
                # find stop_rate
                else :
                    if stop_rate == keeps_rate_long[long_idx][-1] :
                        stop_idx = idx
                        combine_list.append((start_idx, stop_idx))
                        is_start = True
                        long_idx += 1 # next

        combined_list = []
        for start_idx, stop_idx in combine_list :
            portion = math.ceil((keeps_rate_sub[stop_idx][-1] - keeps_rate_sub[start_idx][0]) / limit_rate)
            each_portion_get = math.floor((stop_idx - start_idx) / portion)
            for n_portion in range(portion) :
                start_portion = start_idx
                # last portion get the rest
                stop_portion = start_idx + each_portion_get if n_portion != (portion - 1) else stop_idx
                combined_list.append((start_portion, stop_portion))
                # next
                start_idx = stop_portion

        keeps_rate_shorter = []
        for idx, (start_idx, stop_idx) in enumerate(combined_list):
            start_rate = keeps_rate_sub[start_idx][0]
            # [(.. 27), (27...)]
            if idx + 1 < len(combined_list) and stop_idx == combined_list[idx + 1][0]: 
                stop_rate = keeps_rate_sub[stop_idx][0]
            else:
                stop_rate = keeps_rate_sub[stop_idx][-1]
            keeps_rate_shorter.append((start_rate, stop_rate))

        # keeps_rate_ok + keeps_rate_shorter
        keeps_rate_subtitle = keeps_rate_ok + keeps_rate_shorter
        keeps_rate_subtitle = sorted(keeps_rate_subtitle, key=lambda x: x[0])
        keeps_sec_subtitle = [(self.rate2sec(start_rate), self.rate2sec(stop_rate)) for start_rate, stop_rate in keeps_rate_subtitle]

        return keeps_sec_subtitle
    
    def seconds2timestamp(self, seconds: float) :
        '''
        convert seconds to timestamp format
        '''
        base = str(seconds).split('.')
        msec = base[-1].ljust(3, '0') # add to back 1 -> 001
        sec = base[0].rjust(2, '0') # add to font 2 -> 02
        if int(sec) >= 60 :
            minute = str(int(sec)//60).rjust(2, '0')
            sec = str(int(sec) - (60*int(minute))).rjust(2, '0')
        else :
            minute = '00'
        timestamp = f'00:{minute}:{sec},{msec}'
        return timestamp
    
    def get_srtfile(self, save_path: str, keeps_sec_subtitle: list) :
        ''' 
        save to .srt file
        '''
        if not save_path.endswith('.srt'): save_path += '.srt'
        with open(f'{save_path}', 'w') as file :
            # seconds -> minutes sub | 66.967 -> 01:06,967
            for order, (start_sec, stop_sec) in enumerate(keeps_sec_subtitle, start=1) :
                start_stamp = self.seconds2timestamp(start_sec)
                stop_stamp = self.seconds2timestamp(stop_sec)
                caption = f'{order}\n{start_stamp} --> {stop_stamp}\n{order}\n\n'
                file.write(caption)
        print(f'saved: {save_path}')

if __name__ == '__main__' :
    tsub = Timesub(filepath='video.mp4')
    keeps_sec_subtitle = tsub.get_timesub()
    tsub.get_srtfile('timesub.srt', keeps_sec_subtitle)