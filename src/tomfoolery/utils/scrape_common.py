#! /usr/bin/env python
import re

def console_output(txt):  

    string = ""

    splits = txt.split('"')     
    quotations =  re.findall('"([^"]*)"', txt)
    if quotations:
        for split in splits:
            if split not in quotations:
                string += f'<span style=\"color:white;\">{split}</span>'     
            else:
                string += (f'<span style=\"color:pink;\">{split}</span>') 
        print(string)           
    else: 
        print(f'<span style=\"color:white;\">{txt}</span>')
 