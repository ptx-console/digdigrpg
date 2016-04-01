Contact me: jinjuyu@naver.com

https://digdigrpg.googlecode.com/svn/trunk/!Main.7z DirectX11 Cython Python C++ Bridge Template Source Code(Dual License: LGPL, Creative Commons CC0)

---

Download: SVN checkout. Googlecode does not provide downloads anymore

Win32 Build Environment Python : https://code.google.com/p/digdigrpg/downloads/detail?name=Python26.7z&can=2&q=#makechanges
You just need Mingw32 with it. I kind of don't remember whole building process so you will have hella time figuring it out.

Save it in the directory you want, run it, extract it in the place you want, run "run.bat", wait for about a minute, voila, W/A/S/D keys to move, space bar to jump, i key for inventory and making items. Press i key while inventory is open to cycle through other items. Left mouse button to dig, Right mouse button to place a block. 1~0 keys to access quick bars. Mouse Wheel also works. Tab key to cycle through two quick bars.  ESC key to get out of the inventory mode, Alt + F4 to quit and save game. To reset, delete all of the contents in the "map" folder.



Build Instruction:
This game requires Pygame, PyOpenGL, numpy

Download the SVN and,

1. Install Cython, MinGW

2. modify gen.bat according to your MinGW installation directory

3. run gen.bat

4. run aa.bat

5. run digdig.py

6. Done!




About Linux

You need to install latest development branch of cython to compile under linux.

Also, you need send c99 comilation option to gcc to compile it successfully.






An RPG game set in block digging world

Will support block digging stuffs(already supports digging, stacking, infinite map),
in game scripting,
rpg stuffs,
multiplayer functionality in future plans

I use slow computer(SiS 661FX integrated chipset, opengl 1.4) so FPS is low on the screenshot but it's actually very fast and optimised.

Triple License: LGPL, AGPL, GPL, GPLv2, GPLv3, MIT, Any oss approved license
MEANS: just use it and do whatever you want with it

Download 7zip here: http://www.7-zip.org/

![http://digdigrpg.googlecode.com/svn/trunk/KoreanColor.jpg](http://digdigrpg.googlecode.com/svn/trunk/KoreanColor.jpg)
![http://digdigrpg.googlecode.com/svn/trunk/goldenglass.jpg](http://digdigrpg.googlecode.com/svn/trunk/goldenglass.jpg)
![http://digdigrpg.googlecode.com/svn/trunk/monument.jpg](http://digdigrpg.googlecode.com/svn/trunk/monument.jpg)
![http://digdigrpg.googlecode.com/svn/trunk/asd.jpg](http://digdigrpg.googlecode.com/svn/trunk/asd.jpg)
![http://digdigrpg.googlecode.com/svn/trunk/home.jpg](http://digdigrpg.googlecode.com/svn/trunk/home.jpg)
![http://digdigrpg.googlecode.com/svn/trunk/items.jpg](http://digdigrpg.googlecode.com/svn/trunk/items.jpg)
![http://digdigrpg.googlecode.com/svn/trunk/skill.jpg](http://digdigrpg.googlecode.com/svn/trunk/skill.jpg)
![http://digdigrpg.googlecode.com/svn/trunk/msg.jpg](http://digdigrpg.googlecode.com/svn/trunk/msg.jpg)

You need 7z920.exe to extract .7z files. It's 7-Zip.
You need to download python26.7z and digdigrpg.exe both.
you can extract both files(7z, exe) with 7z. Also you can execute exe file and it will extract.

Yes you can dig and stack and build. There are even torches and chests. You can make pickaxes, axes, shovels. There are wooden pickaxe, stone pickaxe, iron pickaxe, diamond pickaxe. lol.


1. Extract digdigrpg.exe using 7-Zip in the directory you want.
2. Extract python26.7z in the same directory you extracted digdigrpg.exe. Make sure it's not digdigrpg\Python26\Python26. It has to be digdigrpg\Python26.
3. Launch run.bat

If you want farther "view" you can switch G\_FAR = 10.0 to G\_FAR = 300.0 in digdig.py file. I really have slow computer so I narrowed it overly down...

Keys: i key to open inventory and make stuff, you need 5 wood block to make pickaxe and etc. To make an item just have right ingredients in your inventory or quickbar and click one of make icons. You can switch between two quickbars by pressing Tab key. WASD to move around, SPACEBAR to jump.  Also you can only have one save file and it's automatically saved if you exit using ALT+F4...

It's far from finished so it's not actually playable. You can't have multiple save files even though you can save by exiting using ALT+F4 key. But you can build stuff and make screen shot..... but there are far too few kinds of block so it's not really fun to build either.

You can build stuff, you can make few brick blocks with cobblestone block and glass with sand, wood with logs(there are many trees). You can build chests, torches.

You can dig and build with what I made so far but I didn't make water flowing and lava and caves and stuff and there are too few kinds of blocks. About 15 I guess....

And there is no multiplay functionality yet... I kind of made all those in 5 weeks and I got tired really fast so I'm resting so it's not gonna happen any time soon....




Without GOD's help it will not be finished :)
_For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life._