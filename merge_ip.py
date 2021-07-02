# -*- coding: utf-8 -*-

# @File    : merge_ip.py
# @Date    : 2021-07-01
# @Author  : 王超逸
# @Brief   : 一个很高时间复杂度的区间合并算法
"""
[a1,b1) [a2,b2)
not(b1<a2 or a1>b2)
b1>=a2 and a1<=b2
"""
from typing import TextIO
import logging
from copy import copy

logger = logging.getLogger("merge_ip")

SEPARATOR = " "


def int_to_ip(num: int):
    result = []
    while num > 0:
        result.append(num % 256)
        num //= 256
    result.reverse()
    return ".".join(map(str, result))


def ip_to_int(ip: str):
    nums = [i for i in ip.split(".")]
    assert len(nums) == 4
    result = 0
    for i in map(int, nums):
        result *= 256
        result += i
    return result


def get_all_ip(start: str, end: str):
    start = ip_to_int(start)
    end = ip_to_int(end)
    for i in range(start, end):
        yield int_to_ip(i)


def input_ip(file: TextIO):
    ip_range = []
    ip_segment = []
    for line in file:
        if line.find(":") != -1:
            logger.info(f"ipv6地址{line.strip()},跳过")
            continue
        t = line.split(SEPARATOR)
        if len(t) == 2:
            ip_range.append((t[0].strip(), t[1].strip()))
            continue
        t = line.split("/")
        if len(t) == 2:
            ip_segment.append((t[0].strip(), int(t[1])))
            continue
        logger.error(f"{line}格式不对")
    return ip_range, ip_segment


def converse_segment_to_range(ip, mask):
    length = 2 ** mask
    start = ip_to_int(ip) & ~(length-1)
    end = start + length
    start = int_to_ip(start)
    end = int_to_ip(end)
    return start, end


def merge_ip_range(ip_range: list) -> list:
    while True:
        merged = set()
        new = set()
        for i in range(len(ip_range)):
            if ip_range[i] in merged:
                continue
            for j in range(i + 1, len(ip_range)):
                if ip_range[j] in merged:
                    continue
                a1, b1 = ip_range[i]
                a2, b2 = ip_range[j]
                if not (ip_to_int(b1) < ip_to_int(a2) or ip_to_int(a1) > ip_to_int(b2)):
                    merged.add(ip_range[i])
                    merged.add(ip_range[j])
                    new.add((min(a1, a2), max(b1, b2)))
        if new:
            ip_range = list((set(ip_range) - merged) | new)
        else:
            return ip_range


def input_and_merge(file: TextIO):
    ip_range, ip_segment = input_ip(file)
    ip_range += [converse_segment_to_range(ip, mask) for ip, mask in ip_segment]
    return sorted(merge_ip_range(ip_range),key=lambda x:ip_to_int(x[0]))
