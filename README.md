# pixiv-ranking-list-catcher v0.0.1

An naive catcher by Python for the pixiv's ranking list.

## Features

Catch the daily ranking list on a certain day or in a period, and the up-to-date universal ranking list, including illustration and manga.

Reject re-downloading. 

## how to use

Install [python](https://www.python.org)

Save `main.py` to the root of repository that you want to keep those images, and create a file named `cookie` within your cookie for pixiv. Run `main.py` it as

`python main.py [time, [maximum_daily_num, [maximum_universal_num]]]`

`time` indicates a certain day (like 20150327) or a time period (20150327-20150405). If ommited, it will be `tdy`, which denotes to catch the up-to-date ranking list. 

`maximum_daily_num` and `maximum_universal_num` give the maximum number of works to be analysed on the list. They will defaultly be set to 50.

Some extra options are placed in the head of codes.

NOTICE : Universal ranking list will be analysed only when `time` is `tdy`.
