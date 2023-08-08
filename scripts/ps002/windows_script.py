import os
import re
import subprocess
import time

from sdk import AbstractScript, RequireClass, RequireType, TextType

source_path = "windows_1.img.gz"


def part_c_reg(instance, text):
    pattern = r"\d+[GMKB]?$"
    match = re.match(pattern, text)
    if match:
        return None
    else:
        return "输入结果有误，应输入数字，末尾应该为空或[G,M,K]"


class Script(AbstractScript):
    def __init__(self):
        super().__init__()

    def name(self) -> str:
        return "Windows 10 专业版 22h2"

    def info(self) -> str | tuple:
        return "windows安装程序， 您必须遵守Windows相关条款，继续安装则代表接受条款", 'text'

    def req_param(self) -> tuple[RequireClass, ...]:
        return (
            RequireClass("part C size", "设置C盘的大小", RequireType.TEXT, TextType.TEXT, part_c_reg),
            RequireClass("disk", "选择安装磁盘", RequireType.DISK)
        )

    def umount_all(self):
        self.set_text(f"unmount part")
        cmd = f"umount {self.to_path}*"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1,
                                   universal_newlines=True)
        for line in process.stderr:
            self.set_text(line, type="error")

    def write_img(self):
        self.set_text("写入镜像中")
        cmd = f'gzip -dc {os.path.join(os.path.dirname(__file__), source_path)} |sudo dd of={self.to_path} bs=4M status=progress'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1,
                                   universal_newlines=True)
        for line in process.stderr:
            self.set_text(line)

    def delete_part(self, num):
        self.set_text("删除最后分区")
        cmd = f'echo "d\n{num}\nw" | fdisk {self.to_path}'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True)

        for line in process.stdout:
            self.set_text(line)

    def resize_part(self, s):
        self.set_text("设置C盘大小" + s)

        cmd = f'echo "resizepart 3 {s} \n quit" | parted {self.to_path}'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True)

        for line in process.stdout:
            self.set_text(line)

        process.wait()
        cmd = f'echo y |ntfsresize {self.to_path}3'

        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True)

        for line in process.stdout:
            self.set_text(line)

    def new_part(self):
        self.set_text("新建分区")

        cmd = f'echo "n\n\n\n\n t\n4\n11\nw" | fdisk {self.to_path}'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True)
        for line in process.stdout:
            self.set_text(line)

    def format(self):
        self.set_text("格式化分区")

        cmd = 'partprobe'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True)
        for line in process.stdout:
            self.set_text(line)

        cmd = f'mkfs.ntfs -f {self.to_path}4'
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True)
        for line in process.stdout:
            self.set_text(line)

    def script(self):
        # todo:验证镜像
        for i in range(11):
            self.set_percent(i * 0.1)
            self.set_text(f"请稍等")
            time.sleep(0.5)

        res = yield self.dialog("开始安装", RequireClass("confirm", "确定要开始安装吗", RequireType.BOOL))
        if not res:
            self.set_fail("用户取消")
            return

        to_path = self.get_req_parma('disk')
        self.to_path = to_path
        self.umount_all()

        self.write_img()
        self.delete_part(4)
        c_size = self.get_req_parma("part C size")
        self.resize_part(c_size)
        self.new_part()
        self.format()
        self.set_success("安装成功！")
