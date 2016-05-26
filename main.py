#coding=utf-8
from bs4 import BeautifulSoup
from html.parser import HTMLParser
from os.path import join, getsize
import urllib.request, urllib.error, urllib.parse
import os, re, time, sys, json, shutil

domain = 'http://www.pixiv.net/'
headers = {
  'Referer': domain,
  'Cookie' : 'p_ab_id=5; __utmt=1; _gat_UA-77039608-4=1; visit_ever=yes; a_type=0; module_orders_mypage=%5B%7B%22name%22%3A%22everyone_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22spotlight%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22featured_tags%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22contests%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22following_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22mypixiv_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22booth_follow_items%22%2C%22visible%22%3Atrue%7D%5D; hide_premium_promotion_modal_gw=1462606183; login_ever=yes; ki_t=1462606287044%3B1462606287044%3B1462606287044%3B1%3B1; ki_r=; __utma=235335808.1801273321.1462606253.1462606253.1462606253.1; __utmb=235335808.7.9.1462606285323; __utmc=235335808; __utmz=235335808.1462606253.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmv=235335808.|2=login%20ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=14860075=1; _ga=GA1.2.1801273321.1462606253; PHPSESSID=14860075_f92ddc5c1d2c7d12d3d6635e8f2bda7d; device_token=d018e1a88edbc262fcf81c6825998f6a'
}

a_day = 3600 * 24
maximum_period_days = 15
maximum_universal_works = 100
maximum_daily_works = 100
maximum_in_multi_work = 50
maximum_load_log_days = 30

daily_ranking_list_url = domain + 'ranking.php?mode=daily&content=illust'
universal_ranking_list_url = domain + 'ranking_area.php?type=detail&no=6'
manga_big_mode = 'manga_big'
medium_mode = 'medium'
directory = '.'

_time = 'tdy'
daily_num = 2
universal_num = 2

def log(str = '', _end = False):
    if not _end:
        print(str)
    else:
        print(str, end = '', flush = True)

def get(url):
    try:
        request = urllib.request.Request(url, headers = headers)
        res = urllib.request.urlopen(request)
        return res
    except urllib.error.URLError as e:
        print(e.reason)
        return -1

def create_folder(fold_path):
    log('try creating %s...'%fold_path, False)
    if not os.path.exists(fold_path):
        os.makedirs(fold_path)
        log('success.')
    else:
        log(' The fold has been created.')

def image_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 0

def soup(page):
    return BeautifulSoup(page.read(), 'html.parser')

def load_json(file_name):
    file = open(file_name, 'r')
    result = json.loads(file.read())
    file.close()
    return result

def dump_json(pack, file_name):
    file = open(file_name, 'w')
    file.write(json.dumps(pack, sort_keys = True, indent = 2, separators = (',',':')))
    file.close()

def strtotm(_str, _format = '%Y-%m-%d'):
    return time.mktime(time.strptime(_str, _format))

def tmtostr(_time = time.time(), _format = '%Y-%m-%d'):
    return time.strftime(_format, time.localtime(_time))

class pixiv_daily_manager:
    images_lib = {}
    tdy_lib = {}
    multi_ever = {}
    old_mode = False

    dir_main = directory
    dir_log = '%s/log'%dir_main
    dir_tdy = ''
    dir_universal = ''
    dir_daily = ''
    dir_current = ''

    time_diff = a_day * maximum_load_log_days
    init_time = time.time()
    date = ''

    trydown = 0
    success = 0
    fail = 0
    process_num = 0

    def init_count(self):
        self.trydown = 0
        self.success = 0
        self.fail = 0
        self.process_num = 0

    def illust_url(self, id, mode = medium_mode, page = '0'):
        return domain + 'member_illust.php?mode=%s&illust_id=%s&page=%s'%(mode, id, page)

    def ilib(self, id, path, tdy = False):
        self.images_lib[id] = path
        if tdy:
            self.tdy_lib[id] = path

    def lib_exists(self, id):
        return id in self.images_lib and image_exists(self.images_lib[id])

    def erase_log(self, id, path):
        log_file_date = re.search(re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}'), path).group(0)
        log_file = '%s/%s'%(self.dir_log, log_file_date)
        pack = load_json(log_file)
        try:
            os.remove(path)
        except: pass
        try:
            del pack['list'][id]
        except: pass
        if (id.find('-')):
            try:
                os.rmdir(path[:path.rfind('/')])
            except: pass
        dump_json(pack, log_file)

    def update_log(self, file_name):
        pack = load_json('%s/%s'%(self.dir_log, file_name))
        erase_list = {}
        for id, path in pack['list'].items():
            if not image_exists(path):
                self.erase_log(id, path)
                erase_list[id] = path
        for id, path in erase_list.items():
            del pack['list'][id]
        return pack

    def load_log(self):
        log_list = os.listdir(self.dir_log)
        for file_name in log_list:
            try:
                if abs(strtotm(file_name) - self.init_time) > self.time_diff:
                    continue
                pack = self.update_log(file_name)
                self.images_lib.update(pack['list'])
            except: pass

    def print_log(self):
        log_file = self.dir_log + '/' + self.date
        if os.path.exists(log_file):
            try:
                old_lib = load_json(log_file)['list']
                old_lib.update(self.tdy_lib)
                self.tdy_lib = old_lib
            except: pass

        pack = {
            'finished_time' : tmtostr(),
            'list' : self.tdy_lib
        }
        dump_json(pack, log_file)

    def init(self, _date = tmtostr(), old_mode = False):
        self.date = _date
        self.init_time = strtotm(self.date)
        self.old_mode = old_mode
        self.images_lib = {}
        self.tdy_lib = {}

        self.dir_tdy = self.dir_main + '/' + _date
        self.dir_universal = self.dir_tdy + '/universal'
        self.dir_daily = self.dir_tdy + '/daily'

        create_folder(self.dir_log)
        create_folder(self.dir_tdy)
        create_folder(self.dir_universal)
        create_folder(self.dir_daily)

        self.load_log()

        log('end creating the neened environment.')
        log()
        if old_mode:
            log('NOTICE: You are using old-download-mode. The universal ranking won\'t be analysed.')
            time.sleep(3)

    def download_single(self, url, id, subnum = -1):
        multi_mode = subnum >= 0
        subnum = str(subnum)
        process_num = str(self.process_num)
        subpath = id
        lib_id = id
        if multi_mode:
            process_num = process_num + '-' + subnum
            lib_id = lib_id + '-' + subnum
            subpath = subpath + '/' + subnum

        log('processing %s, id=%s : try downloading %s ...'%(process_num, id, url), True)

        type = url[url.rfind('.')+1:]
        path = self.dir_current + '/' + subpath + '.' + type

        if image_exists(path):
            log()
            log('%s has existed.'%lib_id)
            self.ilib(lib_id, path, 1)
            return 1

        if self.lib_exists(lib_id):
            log()
            log('%s has been downloaded to %s.'%(lib_id, self.images_lib[lib_id]))
            self.multi_ever[lib_id] = self.images_lib[lib_id]
            return 0

        self.trydown = self.trydown + 1
        file = open(path, 'wb')
        try:
            file.write(get(url).read())
            file.close()
            self.ilib(lib_id, path, 1)
            self.success = self.success + 1
            self.print_log()
            log('success.')
            return 1
        except:
            self.fail = self.fail + 1
            log('fail')
            return 0

    def download_multiple(self, id, num):
        log('there is a set of images, %d in total'%num)
        if (num > maximum_in_multi_work):
            log('NOTICE: Ignored this work. It contains too many images. there are %d images but the limitation is %d.', num, self.multiple_work_maximum)
            return

        dir_work = self.dir_current + '/' + id
        create_folder(dir_work)
        self.multi_ever = {}
        cnt = 0

        for i in range(0, num):
            page = soup(get(self.illust_url(id, manga_big_mode, i)))
            url = page.find('img')['src']
            cnt = cnt + self.download_single(url, id, i)

        if not cnt:
            os.rmdir(dir_work)
        elif cnt != num and len(self.multi_ever):
            log('WARNING: This set of images was not completely downloaded at once.')
            log('Now try to find the rest locally-saved images.')
            date_list = []
            for id, path in self.multi_ever.items():
                process_num = str(self.process_num) + '-' + id[id.find('-')+1:]
                destination = dir_work + path[path.rfind('/'):]
                log('processing %s, id=%s : move %s to %s...'%(process_num, id[:id.find('-')], path, destination), True)
                shutil.copyfile(path, destination)
                self.erase_log(id, path)
                self.ilib(id, path, 1)
                log('success.')

            for id, path in self.multi_ever.items():
                try:
                     dir = path[:path.rfind('/')]
                     shutil.rmtree(dir, True)
                     os.rmdir(dir)
                except: pass
                log_file_date = re.search(re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}'), path).group(0)
                self.update_log(log_file_date)

    def single(self, url):
        id = re.search(re.compile('illust_id=([0-9]*)'), url).group(1)
        page = soup(get(url))
        try:
            a = re.search(re.compile('<ul class="meta"><li>.*?</li><li>.*?\s(.*?)P</li>'), str(page.find('ul', 'meta'))).group(1)
            return self.download_multiple(id, int(a))
        except:
            return self.download_single(page.find('img', class_ = 'original-image')['data-src'], id)

    def feedback(self):
        log('done! %d pic in total.'%self.trydown)
        log('%d success.'%self.success)
        log('%d fail.'%self.fail)
        log()
        log()

    def universal_analysis(self, num = 50):
        print('catch the universal ranking. preparing...')
        self.init_count()
        self.dir_current = self.dir_universal
        page = soup(get(universal_ranking_list_url))

        for item in page.find_all('div', 'ranking-item'):
            self.process_num = self.process_num + 1
            try:
                a = item.find('div', class_ = 'work_wrapper').find('a')
                self.single(domain + a['href'])
                log()
            except: pass

            num = num - 1
            if (not num): break

        self.feedback()
        self.print_log()

    def daily_analysis(self, num = 50):
        if self.old_mode:
            suf_date = '&date=%s'%self.date.replace('-', '')
        else: suf_date = ''

        print('catch the daily ranking. preparing...')
        self.init_count()
        self.dir_current = self.dir_daily
        page = soup(get(daily_ranking_list_url + suf_date))
        self.current_number = 0
        for item in page.find_all('div', 'ranking-image-item'):
            self.process_num = self.process_num + 1
            try:
                a = item.find('a')
                self.single(domain + a['href'])
                log()
            except: pass

            num = num - 1
            if (not num): break

        self.feedback()
        self.print_log()




catcher = pixiv_daily_manager()

try:
    old_mode = sys.argv[1]
    daily_num = int(sys.argv[2])
    universal_num = int(sys.argv[3])
except: pass

if universal_num > maximum_universal_works or universal_num < 0 or daily_num > maximum_daily_works or daily_num < 0:
    print('parameters is not supported.')
    sys.exit()

if (_time == 'tdy'):
    catcher.init()
    catcher.daily_analysis(daily_num)
    catcher.universal_analysis(universal_num)
elif _time.find('-') >= 0:
    t = re.search(re.compile('([0-9]{4})([0-1][0-9])([0-3][0-9])-([0-9]{4})([0-1][0-9])([0-3][0-9])'), _time)
    try:
        y1 = t.group(1)
        m1 = t.group(2)
        d1 = t.group(3)
        y2 = t.group(4)
        m2 = t.group(5)
        d2 = t.group(6)
    except: pass
    start = strtotm('%s-%s-%s'%(y1,m1,d1))
    end = strtotm('%s-%s-%s'%(y2,m2,d2))
    if (end - start > a_day * maximum_period_days):
        print('The supported time period is utmost %s days.'%maximum_period_days)
        sys.exit()

    while (start < end + 10):
        date = tmtostr(start)
        print("the current date: %s"%date)
        catcher.init(date, True)
        catcher.daily_analysis(daily_num)
        start = start + a_day
else:
    catcher.init(_time, True)
    catcher.daily_analysis(daily_num)
