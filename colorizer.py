
import chars
import json
import math
KEY_COLOR=3#curses.COLOR_YELLOW
COMP_KEY_COLOR=7
STR_COLOR=1#curses.COLOR_GREEN
COMMENT_COLOR=6#curses.COLOR_BLUE
CHAR_COLOR=5#curses.COLOR_RED
NORMAL_COLOR=0
languages={}
try:
    
    with open("languages.json", 'r') as fp:
        languages = json.load(fp)
        if "ai_name" in configs:AI_NAME=configs["ai_name"]
        if "user_name" in configs:USER_NAME=configs["user_name"] 
        if "user_sysprompt" in configs:USER_SYSPROMPT=configs["user_sysprompt"]

except Exception:
    pass

keys=["int","return"]
compiler_key=["main"]
str_s=['"',"'"]
special_char='\\'
mult_comment_char=['/*','*/']
comment='//'
in_comment_line=False
in_str=False
past_str=None
in_comment_mult=False
after_special_char=False
def load_language(lang):
    global keys,str_s,special_char,mult_comment_char,comment,compiler_key
    if lang not in languages:
        return
    if "keywords" in languages[lang]:
        keys=languages[lang]["keywords"]
    if "comment" in languages[lang]:
        comment=languages[lang]["comment"]
    if "mult_comment" in languages[lang]:
        mult_comment_char=languages[lang]["mult_comment"]
    if "string" in languages[lang]:
        str_s=languages[lang]["string"]
    if "special_char" in languages[lang]:
        special_char=languages[lang]["special_char"]
    if "compiler_key" in languages[lang]:
        compiler_key=languages[lang]["compiler_key"]    
comment_box=[]  
def give_color(text,pos:tuple):
    global in_comment_line,in_str,past_str,after_special_char,in_comment_mult   
    current_comment=0
    in_comment_mult=False
    for j,i in enumerate(comment_box):
        if i[0][1]<pos[1]<i[1][1] :
            current_comment=j
            in_comment_mult=True

            break
        elif i[0][1]==pos[1] and i[0][0]<=pos[0]:
            current_comment=j
            in_comment_mult=True

            break
        elif i[1][1]==pos[1] and i[1][0]>=pos[0]:
            current_comment=j
            in_comment_mult=True

            break
    if in_comment_mult:
        if text in mult_comment_char and len(mult_comment_char)>1:
            if text==mult_comment_char[1]:
                in_comment_mult=False
                comment_box[current_comment][1]=pos
                print(comment_box)
        return COMMENT_COLOR
        
    if in_comment_line:
        if text=='\n':
            in_comment_line=False
            return NORMAL_COLOR
        return COMMENT_COLOR
    if in_str:
        if text in str_s and text==past_str:
            past_str=None
            in_str=False
        return STR_COLOR
    if text in chars.chars or text in chars.double_char:
        after_special_char=False
        if text not in str_s and text!=comment and text not in mult_comment_char:
            return CHAR_COLOR
    all_char=True
    
    
    if text in str_s:
        in_str=True
        past_str=text
        return STR_COLOR
    if text==comment:
        in_comment_line=True
        return COMMENT_COLOR
    if len(mult_comment_char)>0:
        if text==mult_comment_char[0]:
            in_comment_mult=True
            comment_box.append([pos,(math.inf,math.inf)])
            return COMMENT_COLOR
    if text=='\\':
        after_special_char=True
        return NORMAL_COLOR
    for i in text:
        if i not in chars.chars:
            all_char= all_char and False
        if all_char:
            return CHAR_COLOR
    if text in keys and not after_special_char:
        return KEY_COLOR
    if text in compiler_key and not after_special_char:
        return COMP_KEY_COLOR
    return NORMAL_COLOR
def reset_state():
    global in_comment_line,in_str,past_str,after_special_char,in_comment_mult
    after_special_char=False
    in_comment_line=False
    in_str=False
    past_str=None
    in_comment_mult=False

def reset_line():
    global in_comment_line,in_str,past_str,after_special_char
    
    after_special_char=False
    in_comment_line=False
    in_str=False
    past_str=None