#! /usr/bin/env python
# inspired by: http://blog.iconfinder.com/detecting-duplicate-images-using-python/

from PIL import Image
from hashlib import md5
import sys, shutil, os, argparse
import json

KEEP_SUFIX = '_KEPT_'
DELETE_SUFIX = '_GONE_'
KEEP = '%s'+KEEP_SUFIX
DELETE = '%s'+DELETE_SUFIX

def dhash(image, hash_size = 8):
    # Grayscale and shrink the image in one step.
    image = image.convert('L').resize(
        (hash_size + 1, hash_size),
        Image.ANTIALIAS,
    )

    pixels = list(image.getdata())

    # Compare adjacent pixels.
    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)

    # Convert the binary array to a hexadecimal string.
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2**(index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0

    return ''.join(hex_string)

class ImgInfo:
    def __init__(self, name, size, cmp_func):
        self.name = name
        self.res = size
        self.cmp_func = cmp_func

    def __lt__(self, other):
        self_val = self.cmp_func(self)
        other_val = self.cmp_func(other)
        return self_val < other_val
    
    def __eq__(self, other):
        self_val = self.cmp_func(self)
        other_val = self.cmp_func(other)
        return self_val == other_val

class ImgHash:
    def __init__(self, val, info, sensitivity=0):
        self.val = val
        self.sensitivity = sensitivity
        self.img_info = info
        
    def __eq__(self, other):
        #Return the Hamming distance between equal-length sequences
        if len(self.val) != len(other.val):
            return false
        hamming_distance = sum(ch1 != ch2 for ch1, ch2 in zip(self.val, other.val))        
        return hamming_distance <= self.sensitivity
        

    def __hash__(self):
        return hash(self.val)
    
    def __str__(self):
        return self.val
    
def resolution(self):
    return self.res[0] * self.res[1]
    
def size(self):
    statinfo = os.stat(self.name)
    return statinfo.st_size


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare images base on perceptual similarity.')
    '''
    parser.add_argument('image_dir', help='image directory', type=str)
    parser.add_argument('duplicate_dir', default='duplicates', help='duplicates directory', type=str)
    '''
    parser.add_argument('class_dir', help='brand directory', type=str)

    parser.add_argument('-c','--cmp', default=resolution,
                        help='compare images by function and keep higher (resolution, size [resolution])')
    parser.add_argument('-s','--sensitivity', default=0, type=int,
                        help='how similar images must be to be considered duplicates (0 - very similar, 5 - shomehow similar)')
    parser.add_argument('-d','--dry_run', action='store_true',
                        help='just print the pairs')
    args = parser.parse_args()

    DUP_FOLDER = './EUR_uniq'

    if args.sensitivity < 0 or args.sensitivity > 5:
        print('Invalid sensitivity value %d (0, 5)', args.sensitivity)
        sys.exit(1)
    
    img_list = []


    out_js = []
    
    count = 0
    duplicates = 0
    for file_name in os.listdir(args.class_dir):
        img_path = os.path.join(args.class_dir, file_name)
        if count % 100 == 0 :
            print(count)
        sys.stdout.flush()
        count += 1
        try:
            img = Image.open(img_path)
            comp = getattr(sys.modules[__name__], args.cmp) if type(args.cmp) is str else args.cmp
             
            ii1 = ImgInfo(img_path, img.size, comp)
            a = ImgHash(dhash(img), ii1, args.sensitivity)
            try:
                index = img_list.index(a)
            except ValueError:
                index = -1
            if index == -1: # hamming_distance comparison using specified sensitivity
                img_list.append(a)
                shutil.copy(ii1.name, os.path.join(DUP_FOLDER, os.path.basename(ii1.name)))

        except IOError:
            print("error processing files: {}".format(sys.exc_info()))

    print("Found {} duplicates".format(duplicates))

