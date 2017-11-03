#!/usr/bin/python3
# -*- coding:utf-8 -*- 

import os
import sys
import http.client
import urllib.parse
import json
import hashlib
import random
from time import sleep
from datetime import datetime

# limit
max_browse_news = 30
max_comment_news = 5
max_share_news = 5

# YQ param
yq_version = 'V2.1.3'

#device
dev_name = 'GT-I8552'
registrationId = 'e7bcfcfcb94e91d52d174ffb26341532'
imei = 'DMfFJEqHRJOLmsf89I0gtg\u003d\u003d'

# servers address & port
login_server = 'common.iyouqu.com.cn:8080'
data_server = 'iyouqu.com.cn:8080'

# locate_1 关东
locate_1 = {'country': '中国', 
            'province': '湖北省', 
            'city': '武汉市', 
            'position': '在烽火科技签到啦！', 
            'longitude': 114.4342, 
            'latitude': 30.5055}

# locate_2 高新四路
locate_2 = {'country': '中国', 
            'province': '湖北省', 
            'city': '武汉市', 
            'position': '在烽火通信高新四路研发中心签到啦！', 
            'longitude': 114.4302, 
            'latitude': 30.4542} 

# comments
comments = ['good', '[强]', 'nice']

# HTTP headers
req_headers = {
    'YQ-Version':yq_version,
    'YQ-Platform':'android',
    'Content-Type':'application/x-www-form-urlencoded',
    'Host':'common.iyouqu.com.cn:8080',
    'Connection':'Keep-Alive',
    'Accept-Encoding':'gzip',
    'User-Agent':'okhttp/3.3.1',}


class YqUser:

    user_file = 'user.txt'

    def __init__(self, mobile, passwd):
        self.mobile = mobile
        self.passwd = passwd_hash(passwd)
        self.cookie_file = self.mobile + '.dat'
        self.group_file = self.mobile + '_group.txt'

        self.load_cookies()
        self.load_work_group()

    def load_cookies(self):
        '''
        Get user login data
        '''
        if os.path.isfile(self.cookie_file) != True:
            self.login()
        
        with open(self.cookie_file, 'r') as f:
            cookies = json.load(f)
        
        self.name = cookies['name']
        self.id = cookies['id']
        self.depart = cookies['depart']
        self.token = cookies['token']

        if self.login_confirm() != True:
            self.login()

    def load_work_group(self):
        '''
        Get user joined work group and save
        '''
        if os.path.isfile(self.group_file) == False:
            self.get_work_group()
        
        self.group_list = dict()

        with open(self.group_file, 'r') as f:
            for line in f.readlines():
                if line[0] == '#':
                    continue
                
                tmp = line.split(':')
                if len(tmp) != 2:
                    continue
                try:
                    id = int(tmp[0])
                    self.group_list[id] = tmp[1].strip('\r\n ')
                except:
                    pass

    def login(self):
        '''
        User login
        '''
        print('user {} login...'.format(self.mobile), end = '', flush = True)
    
        global req_headers
        req_headers['Host'] = login_server
        if 'YQ-Token' in req_headers:
            req_headers.pop('YQ-Token')

        # send mobile
        req_data_val = {'mobile': self.mobile, 'msgId': 'APP127'}
        resp_data = get_resp_data('/app/user/service.do', login_server, req_headers, req_data_val)

        # send password
        req_data_val = {'device': dev_name, 'mobile': self.mobile, 'msgId': 'APP129', 'password': self.passwd,
            'version': yq_version, 'registrationId': registrationId, 'system': '4.4.2', 'systemType': '1', 'pushType':1}
        
        resp_data = get_resp_data('/app/user/service.do', login_server, req_headers, req_data_val)

        self.name = resp_data['resultMap']['userInfo']['name']
        self.id = resp_data['resultMap']['userInfo']['id']
        self.depart = resp_data['resultMap']['userInfo']['orgid']
        self.token = resp_data['resultMap']['userInfo']['usertoken']

        req_headers['YQ-Token'] = self.token

        # send login finished
        req_data_val = {'msgId': 'GET_OFFLINEMSG', 'userId': self.id}
        finish_data = get_resp_data('/app/group/service.do', login_server, req_headers, req_data_val)
       
        # record login cookies to file
        cookies = {'name': self.name, 'id': self.id, 'depart': self.depart, 'token': self.token}

        with open(self.cookie_file, 'w') as f:
            json.dump(cookies, f)

        print('OK', ' ')


    def login_confirm(self):
        '''
        Confirm login data
        '''
        print('user {} login confirm...'.format(self.mobile), end = '', flush = True)

        global req_headers
        req_headers['Host'] = data_server
        req_headers['YQ-Token'] = self.token

        # send login comfirm
        req_data_val = {'msgId': 'APP161', 'userId':self.id}

        try:
            resp_data = get_resp_data('/app/call/service.do', data_server, req_headers, req_data_val)
            if resp_data['resultMap']['record']['mobile'] != self.mobile:
                raise Exception("cookies data invaid")
            
        except Exception as e:
            print('Error: ', e, ' ')
            return False
        
        print('OK', ' ')
        return True


    def get_work_group(self):
        '''
        Get joined work group
        '''
        print('Getting work group...', end='', flush=True)

        req_data_val = {'msgId': 'APP078', 'userId':self.id}
        resp_data = get_resp_data('/app/group/service.do', login_server, req_headers, req_data_val)

        group_list = dict()

        for group in resp_data['resultMap']['objList']:
            if group['type'] == 2:
                group_list[group['id']] = group['name']

        print('OK', ' ')

        with open(self.group_file, 'w') as f:
            f.write('用"#"在行首注释掉不需要签到的圈子{}'.format(os.linesep))
            for group_id, group_name in group_list.items():
                f.write('{}: {}{}'.format(group_id, group_name, os.linesep))
        
        return group_list


    def show_statis(self):
        '''
        Show user's statistic info
        '''
        req_data_val = {'msgId': 'APP063', 'userId':self.id}
        resp_data = get_resp_data('/app/service.do', data_server, req_headers, req_data_val)

        print('Exp: {}, Points: {}\r\n'.format(resp_data['resultMap']['point'], resp_data['resultMap']['treasure']))


    def show_sys_notify(self, not_viewed=False):
        '''
        Show system notify
        '''
        req_data_val = {'userID':self.id, 'msgId': 'APP066', 'index': 0}
        resp_data = get_resp_data('/app/user/service.do', data_server, req_headers, req_data_val)

        for msg in resp_data['resultMap']['messageList']:
            if not_viewed == True and msg['isread'] == 'true':
                continue
            print(msg['createdate'])
            print(msg['content'])
            print('')


    def sign_on(self, locate):
        '''
        Sign on
        '''
        # reload
        self.load_work_group()

        latitude = float('{:6f}'.format(locate['latitude'] + random.random() * 0.001))
        longitude = float('{:6f}'.format(locate['longitude'] + random.random() * 0.001))

        req_data_val = {'city': locate['city'], 'country': locate['country'], 'groupId': '', 'imei': imei, 'userName': self.name, 'userId': self.id, 'msgId':'APP_SIGN', 
            'position': locate['position'], 'province': locate['province'], 'longitude': longitude, 'latitude': latitude}

        print('')
        for group_id, group_name in self.group_list.items():

            print('Sign on: {}...'.format(group_name), end='', flush=True)
            
            req_data_val['groupId'] = str(group_id)
            
            resp_data = get_resp_data('/app/sign/service.do', data_server, req_headers, req_data_val)
            
            print('OK', ' ')
        
        print('')
        
        self.show_statis()


    def get_news_list(self, categoryId, max_count, not_viewed):
        '''
        Get news list
        '''
        print('Geting news list', end='', flush=True)

        news_list = []
        news_id = set()

        req_data_val = {'userId': self.id, 'msgId': 'APP150', 'department': self.depart, 'index': 0, 
            'categoryType': 0, 'categoryId': categoryId}

        # get pages
        index = 0
        while True:
            print('.', end='', flush=True)

            resp_data = get_resp_data('/app/newsActivity/service.do', data_server, req_headers, req_data_val)

            object_list = resp_data['resultMap']['objectList']

            if len(object_list) == 0:
                break

            index = index + len(object_list) + 1
            lastDate = object_list[-1]['createDate']

            # Only news and not viewed, exclude video
            for news in object_list:
                if news['objectType'] == 2 or news['objectType'] == 3:
                    continue
                if not_viewed == True and news['isView'] == True:
                    continue

                if news['id'] in news_id:
                    continue
                news_list.append(news)
                news_id.add(news['id'])
            
            if len(news_list) >= max_count:
                break ;

            req_data_val['index'] = index
            req_data_val['lastDate'] = lastDate

        print('OK', ' ')
        return news_list


    def browse_news(self):
        '''
        Browse nwes
        '''

        # Get news category:all 
        news_list = self.get_news_list(-6, max_browse_news + 10, True)
    
        cnt = 0
        for news in news_list:
            print('Browsing news: {}......'.format(news['title']), end='', flush=True)
            
            try:
                req_data_val = {'msgId': 'APP009', 'objectId': news['id'], 'userId': self.id, 'opinion':0}
                resp_data = get_resp_data('/app/newsActivity/service.do', data_server, req_headers, req_data_val)
            except Exception as e:
                print('Error({})'.format(e), ' ')
            else:
                print('OK', ' ')
                cnt = cnt + 1

            if cnt >= max_browse_news:
                break
            
            sleep(1)
        
        self.show_statis()
    

    def post_comments(self):
        '''
        Post comments on news
        '''

        # Get news category:lastest 
        news_list = self.get_news_list(-1, max_comment_news + 10, False)
        
        cnt = 0
        for news in news_list:
            print('Commenting news: {}......'.format(news['title']), end='', flush=True)

            try:
                req_data_val = {'content': comments[random.randint(0, len(comments)-1)], 'msgId': 'APP039', 
                    'targetId': news['id'], 'targetType': '2', 'userId': self.id}
                resp_data = get_resp_data('/app/service.do', data_server, req_headers, req_data_val)
            except Exception as e:
                print('Error({})'.format(e), ' ')
            else:
                print('OK', ' ')
                cnt = cnt + 1

            if cnt >= max_comment_news:
                break
            
            sleep(1)
        
        self.show_statis()


    def share_news(self):
        '''
        Share news to group
        '''
        
        # Get news category:lastest 
        news_list = self.get_news_list(-1, max_share_news + 10, False)

        cnt = 0
        for news in news_list:
            print('Sharing news: {}......'.format(news['title']), end='', flush=True)
            
            try:
                req_data_val = {'msgId': 'APP065', 'userId': self.id}
                resp_data = get_resp_data('/app/service.do', data_server, req_headers, req_data_val)

                req_data_val = {'content': news['title'], 'userId': self.id, 'groupName':'yq_crack', 'msgId': 'APP083', "isOriginal":False, 'groupId': 2098, 'type': 1, "isForward":False}
                resp_data = get_resp_data('/app/group/service.do', data_server, req_headers, req_data_val)
            except Exception as e:
                print('Error({})'.format(e), ' ')
            else:
                print('OK', ' ')
                cnt = cnt + 1

            if cnt >= max_share_news:
                break
            
            sleep(1)
        
        self.show_statis()
    

    def get_video_list(self, categoryId, index):
        '''
        Get video list
        '''
        print('Getting video list...', end='', flush=True)
        video_list = [] 

        req_data_val = {'userId':self.id, 'department':self.depart, 'msgId':'APP154', 
            'index': index, 'categoryId': + categoryId}

        resp_data = get_resp_data('/app/newsActivity/service.do', data_server, req_headers, req_data_val)

        print('OK', ' ')

        return resp_data['resultMap']['newsList']


    def watch_one_video(self, video, quick):
        '''
        Watch One video
        '''
        if quick == True:
            video_time = 10
        elif video['videoTime'] != 0:
            video_time = video['videoTime']
        else:
            video_time = random.randint(120, 150)

        print('Watching video: {}  author: {} time: {}(s)'.format(video['title'], video['source'], video_time), flush=True)

        now = datetime.today()
        begin_time = '{}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}:{:0>2d}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)

        wait_time(video_time)

        now = datetime.today()
        end_time = '{}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}:{:0>2d}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)

        
        try:
            req_data_val = {'msgId': 'APP009', 'objectId': video['id'], 'userId': self.id, 'opinion':0}
            resp_data = get_resp_data('/app/newsActivity/service.do', data_server, req_headers, req_data_val)

            req_data_val = {'department': self.depart, 'msgId': 'APP008', 'objectId': video['id'], 'orgId': video['orgId'], 'userId': self.id}
            resp_data = get_resp_data('/app/newsActivity/service.do', data_server, req_headers, req_data_val)

            video_data = {'userId':self.id, 'newsId':str(video['id']), 'playBeginTime': begin_time, 'playEndTime': end_time,
                'playTime': str(video_time), 'totalDuration':0, 'totalTime': video_time, 'networkType':1}

            req_data_val = {'dataJson': json.dumps([(video_data)]), 'msgId':'APP110','type':1}
            resp_data = get_resp_data('/app/statis/service.do', data_server, req_headers, req_data_val)

        except Exception as e:
            print('Error({})'.format(e), ' ')
        else:
            print(' complete', ' ')
        
    
    def watch_videos(self, quick=False, not_viewed=True):
        '''
        Watch video, not really watch
        '''
        video_categorys = [15, 16, 17, 18, 19]
        watched_video_id = set()

        for categoryId in video_categorys:
            index = 0
            while True:
                try:
                    video_list = self.get_video_list(categoryId, index)
                except Exception as e:
                    print('Error: ', e, ' ')
                    continue 
                
                if len(video_list) == 0:
                    break 
                index = index + len(video_list)

                for video in video_list:
                    if not_viewed == True and video['isView'] == True:
                        continue
                    
                    if video['id'] in watched_video_id:
                        continue
                    watched_video_id.add(video['id'])
                    self.watch_one_video(video, quick)
                    self.show_statis()
        
        print("All videos watched.")

def passwd_hash(passwd):
    '''
    Return password hash value
    '''
    m = hashlib.md5()
    m.update(passwd.encode())
    
    return m.hexdigest()


def get_resp_data(url, server_addr, req_header, req_data_val):
    ''' 
    Connect to server, send POST data, and 
    get server response data 
    '''
    req_data = urllib.parse.urlencode({'text': req_data_val})
    conn = http.client.HTTPConnection(server_addr, timeout=10)
    conn.request('POST', url, req_data, req_header)
    resp = conn.getresponse()

    # Server return OK 
    if(resp.status != 200):
        raise Exception("server response status={}".format(resp.status))

    resp_data = json.loads(resp.read().decode())

    resp_code = resp_data['code']
    resp_msg = resp_data['message']
   
    # Get message OK
    if(resp_code != '0'):
        raise Exception(resp_msg)
    
    return resp_data

def wait_time(seconds):

    cnt = seconds//10
    for i in range(cnt+1):
        if seconds >= 10:
            sleep(10)
            seconds = seconds - 10
        else:
            sleep(seconds)
        print('>', end='', flush=True)

def main():

    try:
        if os.path.isfile(YqUser.user_file) != True:
            raise Exception('Please create file "{}"'.format(YqUser.user_file))
        
        with open(YqUser.user_file, 'r') as f:
            userinfo = f.readline()
        
        mobile, passwd = userinfo.split(':')
        user = YqUser(mobile.strip(), passwd.strip('\r\n '))
        user.show_statis()

    except Exception as e:
        print('Error: ', e, ' ')
        s = input("\r\nPress Enter to exit.")
        exit(0)

    
    while True:

        print('')
        print('===============================================================')
        print('1. 签到     -- 工作圈: "{}", 地点: 关东烽火科技'.format(user.group_file))
        print('2. 浏览新闻 -- 浏览30条没有浏览过的新闻.')
        print('3. 发表评论 -- 在最新的5条新闻中发表评论.')
        print('4. 分享新闻 -- 将最新的5条新闻的标题分享到"yq_crack"圈子中，需要手动加入圈子.')
        print('5. 观看视频 -- 观看所有没有观看过的视频, 如果没有获取到视频时长，则默认: 120--150s一个.')
        print('6. 日常任务 -- 顺序执行 1 -> 2 -> 3 -> 4 -> 5')
        print('')
        print('7. 加速观看所有视频  -- 观看所有视频，无论是否看过，10s一个.')
        print('8. 正常观看所有视频  -- 观看所有视频，无论是否看过，时间同5.')
        print('9. 加速观看视频      -- 观看所有没有看过的视频，10s一个.')
        print('')
        print('10. 签到          -- 工作圈: "{}", 地点: 高新四路研发中心'.format(user.group_file))
        print('11. 显示系统通知')
        print('')
        print('0. 退出')

        if len(sys.argv) > 1:
            sel = sys.argv[1]
            cmd_param = True
        else:
            sel = input('\r\n请选择: ')
            cmd_param = False
        
        print('')

        try:

            if sel == '1':
                user.sign_on(locate_1)
            elif sel == '2':
                user.browse_news()
            elif sel == '3':
                user.post_comments()
            elif sel == '4':
                user.share_news()
            elif sel == '5':
                user.watch_videos()
            elif sel == '6':
                user.sign_on(locate_1)
                user.browse_news()
                user.post_comments()
                user.share_news()
                user.watch_videos()
            elif sel == '7':
                user.watch_videos(quick=True, not_viewed=False)
            elif sel == '8':
                user.watch_videos(quick=False, not_viewed=False)
            elif sel == '9':
                user.watch_videos(quick=True, not_viewed=True)
            elif sel == '10':
                user.sign_on(locate_2)
            elif sel == '11':
                user.show_sys_notify()
            elif sel == '0':
                exit(0)

        except Exception as e:
            print('Error: ', e, ' ')
            break
        
        if cmd_param != False:
            break
    
    s = input("\r\nPress Enter to exit.")

if __name__ == '__main__':
    main()
