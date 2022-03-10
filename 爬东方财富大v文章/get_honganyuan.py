# @time   : 2022/3/7 12:19
# @Author : XuYu
#!/usr/bin/python3
import os
import requests
import jmespath
import configparser
import time
import zmail
from loguru import logger


base_path = os.path.dirname(os.path.abspath(__file__))
log_path =os.path.join(base_path, "log",str(time.strftime('%m_%d', time.localtime())) + '_info.log')
logger.add(log_path, retention="5 days")


@logger.catch
def get_response(url):
    resp = requests.get(url=url)
    return resp.json()

@logger.catch
def send_mail(title,html):
    server = zmail.server('form_email', 'password')
    mail = {
        'subject': 'xxx发帖了'+"--"+title,
        'content_text': html,
        'from': '爬取xxx发帖'
    }
    server.send_mail(['to_email'],mail)

@logger.catch
def read_ini(key):
    """
    读取配置文件里的时间
    """
    path = os.path.join(base_path,"honganyuan.ini")
    cf = configparser.ConfigParser()
    cf.read(path, encoding="utf-8")
    return cf.get("count", key)

@logger.catch
def write_ini(key,value):
    """
    更新文章时间
    """
    path = os.path.join(base_path,"honganyuan.ini")
    cf = configparser.ConfigParser()
    cf.read(path, encoding="utf-8")
    cf.set("count", key,value)
    cf.write(open(path,"r+",encoding="utf-8"))


@logger.catch
def get_content():
    url = "https://i.eastmoney.com/api/guba/userdynamiclistv2?uid=2565104875628396&pagenum=1&pagesize=10"
    logger.info("开始调用获取新文章")
    respon = get_response(url)
    logger.info("调用获取新文章成功，获得返回值")
    post_time = jmespath.search("result[0].post_publish_time", respon)
    ini_post_time = read_ini("post_time")
    logger.info(f"获取到最新的文章时间{post_time},配置文件中的时间{ini_post_time}")
    if post_time  > ini_post_time:
        title = jmespath.search("result[0].post_title", respon)
        content = jmespath.search("result[0].post_content", respon)
        write_ini("post_time",post_time)
        send_mail(title,content)
        logger.info(f"发现新文章，已发送邮箱，{title}")
    logger.info("没有新文章")

@logger.catch
def get_comment():
    url2 = "https://i.eastmoney.com/api/guba/myreply?pageindex=1&uid=2565104875628396"
    logger.info("开始调用获取新评论")
    respon = get_response(url2)
    logger.info("调用获取新评论成功，获得返回值")
    reply_publish_time = jmespath.search("result.list[0].reply_publish_time", respon)
    ini_time = read_ini("reply_time")
    logger.info(f"判断评论时间是否一致,最新评论的时间{reply_publish_time},配置文件中的时间{ini_time}")
    if reply_publish_time > ini_time:
        reply_text = jmespath.search("result.list[0].reply_text", respon)
        write_ini("reply_time",reply_publish_time)
        send_mail("评论了", reply_text)
        logger.info(f"发现新评论，已发送邮箱，{reply_text}")
    logger.info("没有新评论")


@logger.catch
def main():
    logger.info(f"你执行了我")
    try:
        get_content()
        time.sleep(2)
        get_comment()
    except Exception as e:
        send_mail("出错了", e)

if __name__ == '__main__':
    main()
