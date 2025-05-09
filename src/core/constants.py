from typing import Final
import textwrap

COMMON_IMAGE_SUFFIXES: Final[tuple[str, ...]] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
)

ASCII_LOGO = textwrap.dedent("""
 _____                     _____           _     
|_   _|                   |_   _|         | |    
  | | _ __ ___   __ _       | | ___   ___ | |___ 
  | || '_ ` _ \ / _` |      | |/ _ \ / _ \| / __|
 _| || | | | | | (_| |      | | (_) | (_) | \__ \\
 \___/_| |_| |_|\__, |      \_/\___/ \___/|_|___/
                 __/ |                           
                |___/                            
    """)
