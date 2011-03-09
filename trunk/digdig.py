# -*- coding: utf8 -*-
SW,SH = 640,480
BGCOLOR = (0, 0, 0)

from math import radians 

from OpenGL.GL import *
from OpenGL.GLU import *

import pygame
from pygame.locals import *

import random
import math
import numpy
import pickle
import os

LMB = 1
MMB = 2
RMB = 3
WUP = 4
WDN = 5
g_Textures = []
def glGenTexturesDebug(texnum):
    global g_Textures
    tex = glGenTextures(texnum)
    if tex in g_Textures:
        print 'Error!'
    g_Textures += [tex]
    return tex
def GenId():
    global g_id
    newid = g_id
    g_id += 1
    return newid

class Text:
    def __init__(self):
        pass
            #rects += Text.Write(font, "text", (0, 0), THE_SCREEN)
    def GetSurf(self, font, text, pos, color=(255,255,255), border=False, borderColor=(255,255,255)):
        surf = font.render(text, True, color)
        if border:
            base = font.render(text,True,borderColor)
            border = font.render(text,True,borderColor)
            base.blit(border, pygame.Rect(1,0,base.get_rect().width,base.get_rect().height))
            base.blit(border, pygame.Rect(1,1,base.get_rect().width,base.get_rect().height))
            base.blit(border, pygame.Rect(0,1,base.get_rect().width,base.get_rect().height))

            base.blit(border, pygame.Rect(-1,0,base.get_rect().width,base.get_rect().height))
            base.blit(border, pygame.Rect(-1,-1,base.get_rect().width,base.get_rect().height))
            base.blit(border, pygame.Rect(0,-1,base.get_rect().width,base.get_rect().height))

            base.blit(border, pygame.Rect(1,-1,base.get_rect().width,base.get_rect().height))
            base.blit(border, pygame.Rect(-1,1,base.get_rect().width,base.get_rect().height))
            base.blit(surf, pygame.Rect(0,0,base.get_rect().width,base.get_rect().height))
            surf = base
        rect = pygame.Rect(pos[0], pos[1], surf.get_rect().width, surf.get_rect().height)
        return surf, rect

    def Write(self, font, text, pos, screen, color=(255,255,255), centerpos = None):
        surf = font.render(text, True, color)
        if centerpos:
            x,y,w,h = centerpos
            x += w/2
            y += h/2
            rect = surf.get_rect()
            w2,h2 = rect.width, rect.height
            x -= w2/2
            y -= h2/2
            rect = screen.blit(surf, pygame.Rect(x, y, surf.get_rect().width, surf.get_rect().height))
        else:
            rect = screen.blit(surf, pygame.Rect(pos[0], pos[1], surf.get_rect().width, surf.get_rect().height))
        return [rect]

    def GetSize(self, font, text):
        surf = font.render(text, True, (0,0,0))
        rect = surf.get_rect()
        return rect.width, rect.height

Text = Text()


class SpecialStrings:
    def GetAlphabets(self):
        alphabets = [chr(i) for i in range(ord('a'),ord('z')+1)+range(ord('A'),ord('Z')+1)]
        return alphabets
    def GetNumerics(self):
        numerics = [chr(i) for i in range(ord('0'),ord('9')+1)]
        return numerics
    def GetSpecials(self):
        specialOrdsTup = [(32, 48), (58, 65), (91, 97), (123,127)]
        specialOrds = []
        for tup in specialOrdsTup:
            start, end = tup
            for i in range(start, end):
                specialOrds.append(i)
        specials = [chr(i) for i in specialOrds]
        return specials
SpecialStrings = SpecialStrings()


def DrawQuad(x,y,w,h, color1, color2):
    glDisable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    glColor4ub(*color1)
    glVertex3f(float(x), -float(y+h), 100.0)
    glVertex3f(float(x+w), -float(y+h), 100.0)
    glColor4ub(*color2)
    glVertex3f(float(x+w), -float(y), 100.0)
    glVertex3f(float(x), -float(y), 100.0)
    glEnd()
    glEnable(GL_TEXTURE_2D)


def RenderImg(texID, texupx, texupy, x, y, w, h):
    glBindTexture(GL_TEXTURE_2D, texID)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    glBegin(GL_QUADS)
    glTexCoord2f(texupx, texupy+float(h)/512.0)
    glVertex3f(float(x), -float(y+h), 100.0)

    glTexCoord2f(texupx+float(w)/512.0, texupy+float(h)/512.0)
    glVertex3f(float(x+w), -float(y+h), 100.0)

    glTexCoord2f(texupx+float(w)/512.0, texupy)
    glVertex3f(float(x+w), -float(y), 100.0)

    glTexCoord2f(texupx, texupy)
    glVertex3f(x, -float(y), 100.0)
    glEnd()


class SpawnerGUI(object): # XXX: 스포너를 이용해 건물을 복사하는 기능을 넣자! 스포너 2개로 min,max바운딩 박스 또는 스포너 2개로 x,z의 min max그리고 높이값으로
    # 정해서 최대 128x128x128크기의 오브젝트를 저장하고 다른곳에 복사할 수 있는 기능을 넣자.
    # 스포너 2개로 x,z값을 정하고 그 위치부터 위쪽으로 Y값 몇칸, 아래쪽으로 Y값 몇칸을 정하는게 가장 현실적일 것 같다.
    # 아니면...스포너 2개로 min/max를 정하고 Y값은 그냥 무한으로 0~128까지를 다 저장하도록 만들던지. 선택적으로 일부분만 할 수도 있게 하자. 오버행
    # 같은게 걸리면 골치아프니까.
    # 저장하면 건물 스포너라는 아이템으로 불러올 수 있다.
    # 또한 개인 소유지를 만들 수 있게 하는데 2개 스포너로 x,z를 minmax정하고 위아래로 Y값을 모두 자기 개인 소유지로 정한다.
    # 넓이가 넓을수록 많은 돈이 필요.
    # 개인 소유지에서만 땅을 파서 광물을 얻을 수 있도록 해보자.
    def __init__(self, x,y,w,h, letterW, color=(0,0,0)):
        self.text = ''
        self.rect = x,y,w,h
        self.letterW = letterW
        self.color = color
        self.active = False
        def A():
            pass
        self.func = A
        self.destroyFunc = A
        EMgrSt.BindLDown(self.LDown)
    def LDown(self, t,m,k):
        x,y,w,h = self.rect
        self.active = False
        if AppSt.gui.invShown and AppSt.gui.toolMode == TM_SPAWN:
            if InRect(x,y,30,30, m.x,m.y):
                if self.text:
                    self.func(self.text)
                AppSt.gui.toolMode = TM_TOOL
                AppSt.gui.ShowInventory(False)
                AppSt.guiMode = False
            if InRect(x+30,y,30,30, m.x,m.y):
                AppSt.gui.toolMode = TM_TOOL
                AppSt.gui.ShowInventory(False)
                AppSt.guiMode = False
            if InRect(x+60,y,30,30, m.x,m.y):
                AppSt.gui.toolMode = TM_TOOL
                AppSt.gui.ShowInventory(False)
                AppSt.guiMode = False
                self.destroyFunc()
            if InRect(x,y+30,w,h-30, m.x,m.y):
                self.active = True
                AppSt.gui.ime.SetPrintFunc(self.SetText)
                AppSt.gui.ime.SetText(self.text)
                AppSt.gui.ime.SetActive(self.active)

    def BindDestroy(self, func):
        self.destroyFunc = func
    def Bind(self, func):
        self.func = func
    def SetText(self, text):
        if text:
            leng = 0
            offset = self.rect[2]/self.letterW
            self.text = text[0:offset]
        else:
            self.text = ''

    def Clear(self):
        self.text = ''
    def Update(self, renderer):
        renderer.NewTextObject(self.text, self.color, (self.rect[0], self.rect[1]+30))

    def Render(self):
        # 선택한 텍스트는 하이라이트 DrawQuad로
        if AppSt.gui.invShown and AppSt.gui.toolMode == TM_SPAWN:
            DrawQuad(*self.rect+((40,40,40,220), (40,40,40,220)))
            x,y,w,h = self.rect
            DrawQuad(x,y+30,w,h-30,(230,230,230,220), (230,230,230,220))

            texupx = (3*30.0) / 512.0
            texupy = (11*30.0) / 512.0
            RenderImg(AppSt.gui.tooltex, texupx, texupy, x+0, y, 30, 30)
            texupx = (3*30.0) / 512.0
            texupy = (12*30.0) / 512.0
            RenderImg(AppSt.gui.tooltex, texupx, texupy, x+30, y, 30, 30)
            texupx = (3*30.0) / 512.0
            texupy = (13*30.0) / 512.0
            RenderImg(AppSt.gui.tooltex, texupx, texupy, x+60, y, 30, 30)

        # ok버튼을 넣고 스포너에 이름을 붙일 수 있도록 한다.
        # 스포너를 좌측 버튼으로 hit 하면 OnSpawnerHit이벤트가 발생하고
        # 코드블럭을 좌측버튼으로 hit하면 OnCodeHit이벤트가 발생한다.

class FileSelector(object):
    def __init__(self, scriptPath):
        self.path = scriptPath
        self.rect = (SW-400)/2, (SH-300)/2, 400, 300
        x,y,w,h = self.rect
        self.lineH = 14
        self.textArea = TextArea(x,y+30,w,h,14,self.lineH,color=(255,255,255),lineCut=False)
        self.textArea.SetText("fileName.py")
        EMgrSt.BindMotion(self.Motion)
        EMgrSt.BindLDown(self.LDown)
        self.selectedFile = -1
        self.pageIdx = 0
        self.dirs = []

        def a(fileN):
            print fileN
        def b():
            pass
        self.func = a
        self.destroyFunc = b

        paths = []
        files = []
        dirs = os.listdir(self.path)
        self.fileLen = (300-30)/self.lineH
        self.pageLen = len(dirs)/(self.fileLen)+1
        self.selectedFileName = None
        self.pageIdx = 0


    def BindDestroy(self, func):
        self.destroyFunc = func
    def Bind(self, func):
        self.func = func

    def LDown(self, t, m, k):
        if AppSt.gui.invShown and AppSt.gui.toolMode == TM_CODE:
            x,y,w,h = self.rect
            if InRect(x,y,w,h,m.x,m.y):
                if InRect(x,y,30,30,m.x,m.y): # prev
                    self.pageIdx -= 1
                    if self.pageIdx < 0:
                        self.pageIdx = 0
                elif InRect(x+30,y,30,30,m.x,m.y): # next
                    self.pageIdx += 1
                    if self.pageIdx >= self.pageLen:
                        self.pageIdx = self.pageLen-1
                elif InRect(x+60,y,30,30,m.x,m.y): # up
                    if self.dirs:
                        del self.dirs[-1]
                    thepath = self.path
                    for path in self.dirs:
                        thepath += "/"+path
                    dirs = os.listdir(thepath)
                    self.pageLen = len(dirs)/(self.fileLen)+1
                    self.pageIdx = 0
                elif InRect(x+90,y,30,30,m.x,m.y): # ok
                    self.func(self.selectedFileName)
                    AppSt.gui.toolMode = TM_TOOL
                    AppSt.gui.ShowInventory(False)
                    AppSt.guiMode = False
                elif InRect(x+120,y,30,30,m.x,m.y): # cancel
                    AppSt.gui.toolMode = TM_TOOL
                    AppSt.gui.ShowInventory(False)
                    AppSt.guiMode = False
                elif InRect(x+150,y,30,30,m.x,m.y): # destroy
                    AppSt.gui.toolMode = TM_TOOL
                    AppSt.gui.ShowInventory(False)
                    AppSt.guiMode = False
                    self.destroyFunc()
                elif self.selectedFile != -1:
                    paths = []
                    files = []
                    thepath = self.path
                    for path in self.dirs:
                        thepath += "/"+path
                    dirs = os.listdir(thepath)
                    paths = []
                    files = []
                    for path in dirs:
                        if os.path.isdir(self.path+"/"+path):
                            paths += [path]
                        elif path.endswith(".py"):
                            files += [path]
                    if self.selectedFile < len(paths+files):


                        selected = (paths+files)[self.pageIdx*(self.fileLen):self.pageIdx*(self.fileLen)+self.fileLen][self.selectedFile]
                        if os.path.isdir(thepath+"/"+selected):
                            self.dirs += [selected]
                            self.pageIdx = 0
                            dirs = os.listdir(thepath+"/"+selected)
                            self.pageLen = len(dirs)/(self.fileLen)+1
                        else:
                            self.selectedFileName = thepath+"/"+selected

    def Motion(self, t, m, k):
        if AppSt.gui.invShown and AppSt.gui.toolMode == TM_CODE:
            self.selectedFile = -1
            x,y,w,h = self.rect
            if InRect(x,y,w,h,m.x,m.y):
                yy = y+30
                idx = 0
                while idx < self.fileLen:
                    if InRect(x,yy+3,w,self.lineH, m.x, m.y):
                        self.selectedFile = idx
                        break
                    idx += 1
                    yy += self.lineH

    def Update(self, renderer):
        paths = []
        files = []
        thepath = self.path
        for path in self.dirs:
            thepath += "/"+path
        dirs = os.listdir(thepath)
        for path in dirs:
            if os.path.isdir(self.path+"/"+path):
                paths += ["[%s]" % path]
            elif path.endswith(".py"):
                files += [path]

        self.textArea.SetText('\n'.join((paths+files)[self.pageIdx*(self.fileLen):self.pageIdx*(self.fileLen)+self.fileLen]))
        self.textArea.Update(renderer)
        renderer.NewTextObject(str(self.selectedFileName), (200,200,200), (self.rect[0]+180, self.rect[1]+0))

    def Render(self):
        # 선택한 텍스트는 하이라이트 DrawQuad로
        DrawQuad(*self.rect+((40,40,40,220), (40,40,40,220)))
        x,y,w,h = self.rect
        if self.selectedFile != -1:
            DrawQuad(x,y+30+3+self.lineH*self.selectedFile,w,self.lineH,(0,0,0,220), (0,0,0,220))

        texupx = (3*30.0) / 512.0
        texupy = (8*30.0) / 512.0
        RenderImg(AppSt.gui.tooltex, texupx, texupy, x, y, 30, 30)
        texupx = (3*30.0) / 512.0
        texupy = (9*30.0) / 512.0
        RenderImg(AppSt.gui.tooltex, texupx, texupy, x+30, y, 30, 30)
        texupx = (3*30.0) / 512.0
        texupy = (10*30.0) / 512.0
        RenderImg(AppSt.gui.tooltex, texupx, texupy, x+60, y, 30, 30)
        texupx = (3*30.0) / 512.0
        texupy = (11*30.0) / 512.0
        RenderImg(AppSt.gui.tooltex, texupx, texupy, x+90, y, 30, 30)
        texupx = (3*30.0) / 512.0
        texupy = (12*30.0) / 512.0
        RenderImg(AppSt.gui.tooltex, texupx, texupy, x+120, y, 30, 30)
        texupx = (3*30.0) / 512.0
        texupy = (13*30.0) / 512.0
        RenderImg(AppSt.gui.tooltex, texupx, texupy, x+150, y, 30, 30)

class TextArea(object):
    def __init__(self, x,y,w,h, letterW, lineH, color=(0,0,0), lineCut=True):
        self.lines = []
        self.rect = x,y,w,h
        self.letterW = letterW
        self.lineH = lineH
        self.color = color
        self.lineCut = lineCut
    def SetText(self, text):
        if text:
            if self.lineCut:
                leng = 0
                offset = self.rect[2]/self.letterW
                while leng < len(text):
                    newtext = text[leng:leng+offset]
                    self.lines += newtext.split("\n")
                    leng += offset
            else:
                self.lines = text.split("\n")
        else:
            self.lines = []

    def Clear(self):
        self.lines = []
    def Update(self, renderer):
        y = 0
        for text in self.lines:
            renderer.NewTextObject(text, self.color, (self.rect[0], self.rect[1]+y))
            y += self.lineH
            if y > self.rect[3]:
                return

class DynamicTextRenderer(object):
    # 한 씬에 렌더할 텍스트를 모아두고 한번에 렌더링을 하며
    # 0.25초당 한번씩 업데이트 된다.
    # 음....512짜리 4장 정도면 화면 꽉차니까 그거만 만들고 모자라면 더이상 추가하지 않는다.
    def __init__(self, font):
        self.font = font
        self.surfs = []
        for i in range(4):
            texid = glGenTexturesDebug(1)
            self.surfs += [[pygame.Surface((512,512), flags=SRCALPHA), texid, True]]
        self.surfIdx = 0
        self.texts = []
        EMgrSt.BindTick(self.RegenTex)
    def NewTextObject(self, text, color, pos, border=False, borderColor = (255,255,255)):
        if self.surfIdx >= 4:
            return
        if self.texts:
            prevsurfid, prevtextposList, prevpos = self.texts[-1]
            prevsurf = self.surfs[prevsurfid][0]
        else:
            prevsurfid = 0
            prevsurf, texid, updated = self.surfs[0]
            updated = True
            prevtextposList = [[0,0,0,0]]
        textsurf = Text.GetSurf(self.font, text, (0, 0), color, border, borderColor)[0]
        if textsurf.get_height()*((textsurf.get_width()/512)+1) >= 512:
            return None

        x,y,w,h = prevtextposList[-1]
        surf = prevsurf
        surfid = prevsurfid
        x = x+w
        w = textsurf.get_width()
        h = textsurf.get_height()
        
        availLen = 512-x
        needLen = w-availLen
        if needLen > 0:
            needYNum = needLen/512
            if y+needYNum*h >= 512:
                self.surfIdx += 1
                if self.surfIdx >= 4:
                    return
                surf = self.surfs[self.surfIdx][0]
                surfid = self.surfIdx
        self.surfs[self.surfIdx][2] = True

        newtextposList = []
        xx = 0
        if needLen <= 0:
            surf.fill((0,0,0,0), pygame.Rect(x,y,w,h))
            surf.blit(textsurf, pygame.Rect(x,y,w,h), pygame.Rect(xx,0,w,h))
            newtextposList += [[x,y,w,h]]
        else:
            surf.fill((0,0,0,0), pygame.Rect(x,y,availLen,h))
            surf.blit(textsurf, pygame.Rect(x,y,availLen,h), pygame.Rect(xx,0,availLen,h))
            newtextposList += [[x,y,availLen,h]]
            curTextX = availLen
            xx += availLen
            x = 0
            y += h
            while True: 
                if needLen <= 512:
                    surf.fill((0,0,0,0), pygame.Rect(x,y,needLen,h))
                    surf.blit(textsurf, pygame.Rect(x,y,needLen,h), pygame.Rect(xx,0,needLen,h))
                    newtextposList += [[x,y,needLen,h]]
                    break
                else:
                    surf.fill((0,0,0,0), pygame.Rect(x,y,512,h))
                    surf.blit(textsurf, pygame.Rect(x,y,512,h), pygame.Rect(xx,0,512,h))
                    newtextposList += [[x,y,512,h]]
                    xx += 512
                    x = 0
                    y += h
                    needLen -= 512
        self.texts += [[surfid, newtextposList, pos]]

    def Clear(self): # 걍 무조건 1초에 4번 불린다. 아니면 3번 불리던가.
        self.texts = []
        self.surfIdx = 0
    def Render(self):
        textid = 0
        for text in self.texts:
            surfid, poslist, pos = text
            self.RenderText(textid, pos)
            textid += 1
    def RegenTex(self, t,m,k):
        if AppSt.regenTex:
            for idx in range(len(self.surfs)):
                self.surfs[idx][1] = glGenTexturesDebug(1)
                self.surfs[idx][2] = True
    def RenderText(self, textid, pos):
        surfid, posList, pos = self.texts[textid]
        surf, texid, updated = self.surfs[surfid]
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)


        if updated:
            teximg = pygame.image.tostring(surf, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, texid)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
            self.surfs[surfid][2] = False

        glBegin(GL_QUADS)
        xx,yy = pos
        for imgpos in posList:
            x,y,w,h = imgpos
            glTexCoord2f(float(x)/512.0, float(y+h)/512.0)
            glVertex3f(float(xx), -float(yy+h), 100.0)

            glTexCoord2f(float(x+w)/512.0, float(y+h)/512.0)
            glVertex3f(float(xx+w), -float(yy+h), 100.0)

            glTexCoord2f(float(x+w)/512.0, float(y)/512.0)
            glVertex3f(float(xx+w), -float(yy), 100.0)

            glTexCoord2f(float(x)/512.0, float(y)/512.0)
            glVertex3f(float(xx), -float(yy), 100.0)
            xx += w

        glEnd()


class StaticTextRenderer(object):
    # 아이템 숫자 표시는.... 여기서 0~9를 렌더링 한 후에 그 숫자를 가지고 렌더링한다!
    def __init__(self, font):
        self.font = font
        texid = glGenTexturesDebug(1)
        self.surfs = [[pygame.Surface((512,512), flags=SRCALPHA), texid, True]]
        self.texts = []
        EMgrSt.BindTick(self.RegenTex)
    def NewTextObject(self, text, color, border=False, borderColor = (255,255,255)):
        if self.texts:
            prevsurfid, prevtextposList = self.texts[-1]
            prevsurf = self.surfs[prevsurfid][0]
        else:
            prevsurfid = 0
            prevsurf, texid, updated = self.surfs[0]
            prevtextposList = [[0,0,0,0]]
        textsurf = Text.GetSurf(self.font, text, (0, 0), color, border, borderColor)[0]
        if textsurf.get_height()*((textsurf.get_width()/512)+1) >= 512:
            return None

        x,y,w,h = prevtextposList[-1]
        surf = prevsurf
        surfid = prevsurfid
        x = x+w

        w = textsurf.get_width()
        h = textsurf.get_height()
        
        availLen = 512-x
        needLen = w-availLen
        if needLen > 0:
            needYNum = needLen/512
            if y+needYNum*h >= 512:
                texid = glGenTexturesDebug(1)
                self.surfs += [[pygame.Surface((512,512), flags=SRCALPHA), texid, True]]
                surf = self.surfs[-1]
                surfid = len(self.surfs)-1
            else:
                self.surfs[prevsurfid][2] = True

        newtextposList = []
        xx = 0
        if needLen <= 0:
            surf.fill((0,0,0,0), pygame.Rect(x,y,w,h))
            surf.blit(textsurf, pygame.Rect(x,y,w,h), pygame.Rect(xx,0,w,h))
            newtextposList += [[x,y,w,h]]
        else:
            surf.fill((0,0,0,0), pygame.Rect(x,y,availLen,h))
            surf.blit(textsurf, pygame.Rect(x,y,availLen,h), pygame.Rect(xx,0,availLen,h))
            newtextposList += [[x,y,availLen,h]]
            curTextX = availLen
            xx += availLen
            x = 0
            y += h
            while True: 
                if needLen <= 512:
                    surf.fill((0,0,0,0), pygame.Rect(x,y,needLen,h))
                    surf.blit(textsurf, pygame.Rect(x,y,needLen,h), pygame.Rect(xx,0,needLen,h))
                    newtextposList += [[x,y,needLen,h]]
                    break
                else:
                    surf.fill((0,0,0,0), pygame.Rect(x,y,512,h))
                    surf.blit(textsurf, pygame.Rect(x,y,512,h), pygame.Rect(xx,0,512,h))
                    newtextposList += [[x,y,512,h]]
                    xx += 512
                    x = 0
                    y += h
                    needLen -= 512
        self.texts += [[surfid, newtextposList]]
        return len(self.texts)-1

    def RegenTex(self, t,m,k):
        if AppSt.regenTex:
            for idx in range(len(self.surfs)):
                self.surfs[idx][1] = glGenTexturesDebug(1)
                self.surfs[idx][2] = True

    def RenderText(self, textid, pos):
        surfid, posList = self.texts[textid]
        surf, texid, updated = self.surfs[surfid]
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)


        if updated:
            glBindTexture(GL_TEXTURE_2D, texid)
            teximg = pygame.image.tostring(surf, "RGBA", 0) 
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
            self.surfs[surfid][2] = False

        glBegin(GL_QUADS)
        xx,yy = pos
        for imgpos in posList:
            x,y,w,h = imgpos
            glTexCoord2f(float(x)/512.0, float(y+h)/512.0)
            glVertex3f(float(xx), -float(yy+h), 100.0)

            glTexCoord2f(float(x+w)/512.0, float(y+h)/512.0)
            glVertex3f(float(xx+w), -float(yy+h), 100.0)

            glTexCoord2f(float(x+w)/512.0, float(y)/512.0)
            glVertex3f(float(xx+w), -float(yy), 100.0)

            glTexCoord2f(float(x)/512.0, float(y)/512.0)
            glVertex3f(float(xx), -float(yy), 100.0)
            xx += w

        glEnd()

g_id = 0
ITEM_PICKAXE = GenId()
ITEM_AXE = GenId()
ITEM_SHOVEL = GenId()
ITEM_TORCH = GenId()
ITEM_CHARCOAL = GenId()
ITEM_COAL = GenId()
ITEM_STICK = GenId()
ITEM_CHEST = GenId()
ITEM_GOLD = GenId()
ITEM_SILVER = GenId()
ITEM_IRON = GenId()
ITEM_DIAMOND = GenId()
ITEM_STAIR = GenId()
ITEM_WOODENSTAIR = GenId()
ITEM_SWORD = GenId()
ITEM_SPEAR = GenId()
ITEM_MACE = GenId()
ITEM_KNUCKLE = GenId()
ITEM_SHIELD = GenId()
ITEM_GLOVES = GenId()
ITEM_BOOTS = GenId()
ITEM_GOLDRING = GenId()
ITEM_GOLDNECLACE = GenId()
ITEM_HELM = GenId()
ITEM_ARMOR = GenId()
ITEM_SILVERRING = GenId()
ITEM_SILVERNECLACE = GenId()
ITEM_DIAMONDRING = GenId()
ITEM_DIAMONDNECLACE = GenId()
ITEM_SCROLL = GenId()
ITEM_ENCHANTSCROLL = GenId()
ITEM_NONE = 0
TOOL_TEX_COORDS = [
        0,0,
        1,0,
        2,0,
        4,0,
        6,0,
        6,0,
        5,0,
        3,5,
        6,0,
        6,0,
        6,0,
        6,0,
        4,1,
        4,1,
        0,1,
        0,2,
        0,3,
        0,4,
        0,5,
        1,1,
        1,2,
        1,3,
        1,4,
        1,5,
        2,1,
        1,3,
        1,4,
        2,2,
        2,3,
        0,6,
        0,7,
        ]

TYPE_BLOCK = "Block"
TYPE_ITEM = "Item"

"""
무기
방패
모자
몸통
장갑
신발
목걸이
반지
"""
g_id = 0
EQ_RIGHTHAND = GenId()
EQ_LEFTHAND = GenId()
EQ_HEAD = GenId()
EQ_BODY = GenId()
EQ_GLOVES = GenId()
EQ_BOOTS = GenId()
EQ_NECKLACE = GenId()
EQ_RING = GenId()
g_id = 0
WEAPON_ONEHANDED = GenId()
WEAPON_TWOHANDED = GenId()


g_id = 0
TM_TOOL = GenId()
TM_EQ = GenId()
TM_BOX = GenId()
TM_CODE = GenId()
TM_SPAWN = GenId()
TM_CHAR = GenId()
TM_SKILL = GenId()
TM_ENCHANT = GenId()


class MakeTool(object):
    def __init__(self, name, desc, color, needs, returns, textRenderer, textRendererSmall):
        self.name = name
        self.desc = desc
        self.color = color
        self.needs = needs
        self.returns = returns
        self.textidName = [textRenderer.NewTextObject(text, (0,0,0)) for text in self.name.split("\n")]
        self.textidDesc = [textRendererSmall.NewTextObject(text, (0,0,0)) for text in self.desc.split("\n")]
class DigDigGUI(object):
    def __init__(self):
        self.invPos = (SW-306)/2, 430-186-20
        self.qbarPos = (SW-308)/2, 430
        self.makePos = (SW-306)/2, 20-3
        self.invRealPos = (SW-300)/2, 430-186-20+3
        self.qbarRealPos = (SW-300)/2, 430+4
        self.makeRealPos = (SW-300)/2, 20

        self.inventex = texture = glGenTexturesDebug(1)
        self.invenimg = pygame.image.load("./images/digdig/inven.png")
        glBindTexture(GL_TEXTURE_2D, self.inventex)
        teximg = pygame.image.tostring(self.invenimg, "RGBA", 0) 
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)

        self.tooltex = texture = glGenTexturesDebug(1)
        self.toolimg = pygame.image.load("./images/digdig/tools.png")
        glBindTexture(GL_TEXTURE_2D, self.tooltex)
        teximg = pygame.image.tostring(self.toolimg, "RGBA", 0) 
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)


        self.invShown = False
        self.setInvShown = False
        self.toolMode = TM_TOOL # 장비창이냐 제작창이냐 상자창이냐 등등
        self.font = pygame.font.Font("./fonts/Fanwood.ttf", 18)
        self.font2 = pygame.font.Font("./fonts/FanwoodText-Italic.ttf", 13)
        self.font3 = pygame.font.Font("./fonts/Fanwood.ttf", 14)
        self.textRenderer = StaticTextRenderer(self.font)
        self.textRendererSmall = StaticTextRenderer(self.font2)
        self.textRendererArea = DynamicTextRenderer(self.font3)
        #self.testText = TextArea(0,30,640,400, 16, 16)
        self.testFile = FileSelector("./scripts")
        self.testEdit = SpawnerGUI((SW-400)/2,(SH-50)/2,400,50,14)
        #self.testText.SetText(u"asdhoihhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhrrㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱrrㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱㄱ가가가가\nadsasd")
        self.prevAreaT = 0
        self.areaDelay = 500
        self.numbers = [self.textRenderer.NewTextObject(`i`, (255,255,255), True, (0,0,0)) for i in range(10)]



        self.draggingItem = None
        self.dragging = False
        self.dragPos = None
        self.dragCont = None
        self.otherPoints = [] # 땅에 떨굴 때 사용하는 영역
        self.selectedItem = 0
        self.selectedMakeTool = -1
        self.selectedContItem = ITEM_NONE

        EMgrSt.BindTick(self.Tick)
        EMgrSt.BindMotion(self.Motion)
        EMgrSt.BindLDown(self.LDown)
        EMgrSt.BindRDown(self.RDown)
        EMgrSt.BindLUp(self.LUp)
        EMgrSt.BindRUp(self.RUp)
        EMgrSt.BindKeyDown(self.KDown)
        EMgrSt.BindWUp(self.WUp)
        EMgrSt.BindWDn(self.WDn)
        self.ime = CustomIMEModule(self.OnIME)
        self.slotSize = slotSize = 30

        try:
            self.inventory = pickle.load(open("./map/inv.pkl", "r"))
        except:
            self.inventory = [ITEM_NONE for i in range(60)]
        try:
            self.qbar = pickle.load(open("./map/qb.pkl", "r"))
        except:
            self.qbar = [ITEM_NONE for i in range(10)]

        try:
            self.boxes = pickle.load(open("./map/chests.pkl", "r"))
        except:
            self.boxes = {}
        try:
            self.codes = pickle.load(open("./map/codes.pkl", "r"))
        except:
            self.codes = {}
        try:
            self.spawns = pickle.load(open("./map/spawns.pkl", "r"))
        except:
            self.spawns = {}
        try:
            self.eqs = pickle.load(open("./map/eqs.pkl", "r"))
        except:
            self.eqs = [ITEM_NONE for i in range(8)]


        
        eqTexts = [
        u"RightHand",
        u"LeftHand",
        u"Head",
        u"Body",
        u"Gloves",
        u"Boots",
        u"Necklace",
        u"Ring",]
        self.eqTexts = []
        for t in eqTexts:
            self.eqTexts += [self.textRendererSmall.NewTextObject(t, (0,0,0))]
        


        self.makes = [ITEM_NONE for i in range(60)]
        self.makes[0] = MakeTool(u"Wood", u"A wood block.", (116,100,46), [(BLOCK_LOG, 1, TYPE_BLOCK)], (BLOCK_WOOD, [], [], 4, TYPE_BLOCK), self.textRenderer, self.textRendererSmall)
        self.makes[1] = MakeTool(u"Stick", u"Multi purpose stick", (255,255,255), [(BLOCK_WOOD, 1, TYPE_BLOCK)], (ITEM_STICK, [], [], 4, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[2] = MakeTool(u"Charcoal", u"A charcoal", (60,60,60), [(BLOCK_LOG, 1, TYPE_BLOCK)], (ITEM_CHARCOAL, [], [], 1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[3] = MakeTool(u"Glass", u"A glass", (255,255,255), [(BLOCK_SAND, 1, TYPE_BLOCK)], (BLOCK_GLASS, [], [], 1, TYPE_BLOCK), self.textRenderer, self.textRendererSmall)
        self.makes[4] = MakeTool(u"Stone", u"A stone block", (255,255,255), [(BLOCK_COBBLESTONE, 1, TYPE_BLOCK)], (BLOCK_STONE, [], [], 1, TYPE_BLOCK), self.textRenderer, self.textRendererSmall)
        self.makes[5] = MakeTool(u"Brick", u"A brick block", (255,255,255), [(BLOCK_COBBLESTONE, 1, TYPE_BLOCK)], (BLOCK_BRICK, [], [], 1, TYPE_BLOCK), self.textRenderer, self.textRendererSmall)
        self.makes[6] = MakeTool(u"Wall", u"A wall block", (255,255,255), [(BLOCK_COBBLESTONE, 1, TYPE_BLOCK)], (BLOCK_BRICK, [], [], 1, TYPE_BLOCK), self.textRenderer, self.textRendererSmall)
        self.makes[7] = MakeTool(u"TNT", u"Kaboom! - Machine -", (255,255,255), [(BLOCK_GRAVEL, 1, TYPE_BLOCK)], (BLOCK_TNT, [], [], 1, TYPE_BLOCK), self.textRenderer, self.textRendererSmall)
        self.makes[13] = MakeTool(u"Wooden stair", u"A wooden stair", (116,100,46), [(BLOCK_WOOD, 1, TYPE_BLOCK)], (ITEM_WOODENSTAIR, [], [], 1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[14] = MakeTool(u"Stair", u"A stair", (30,30,30), [(BLOCK_COBBLESTONE, 1, TYPE_BLOCK)], (ITEM_STAIR, [], [], 1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[20] = MakeTool(u"Wooden pickaxe", u"Used to pick stones, ores", (116,100,46), [(BLOCK_WOOD, 5, TYPE_BLOCK)], (ITEM_PICKAXE, [15,20], (BLOCK_IRONORE, BLOCK_SILVERORE, BLOCK_GOLDORE, BLOCK_DIAMONDORE), 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        # returns: 아이템, 체력깎는 정도, 못파는 광물목록
        self.makes[21] = MakeTool(u"Wooden axe", u"Wood cutting wooden axe", (116,100,46), [(BLOCK_WOOD, 5, TYPE_BLOCK)], (ITEM_AXE, [15,20], [], 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[22] = MakeTool(u"Wooden shovel", u"Digs up dirts or sands", (116,100,46), [(BLOCK_WOOD, 5, TYPE_BLOCK)], (ITEM_SHOVEL, [15,20], [], 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[23] = MakeTool(u"Stone pickaxe", u"Used to pick stones, ores", (47,43,43), [(BLOCK_COBBLESTONE, 5, TYPE_BLOCK)], (ITEM_PICKAXE, [20,10], (BLOCK_IRONORE, BLOCK_SILVERORE, BLOCK_GOLDORE, BLOCK_DIAMONDORE), 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        # returns: 아이템, 체력깎는 정도, 못파는 광물목록
        self.makes[24] = MakeTool(u"Stone axe", u"Used to cut trees", (47,43,43), [(BLOCK_COBBLESTONE, 5, TYPE_BLOCK)], (ITEM_AXE, [20,10], [], 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[25] = MakeTool(u"Stone shovel", u"Digs up dirts or sands", (47,43,43), [(BLOCK_COBBLESTONE, 5, TYPE_BLOCK)], (ITEM_SHOVEL, [20,10], [], 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[26] = MakeTool(u"Iron pickaxe", u"Used to pick stones, ores", (107,107,107), [(ITEM_IRON, 5, TYPE_ITEM, (107,107,107))], (ITEM_PICKAXE, [40,5], (BLOCK_IRONORE, BLOCK_SILVERORE, BLOCK_GOLDORE, BLOCK_DIAMONDORE), 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        # returns: 아이템, 체력깎는 정도, 못파는 광물목록
        self.makes[27] = MakeTool(u"Iron axe", u"Used to cut trees", (107,107,107), [(ITEM_IRON, 5, TYPE_ITEM, (107,107,107))], (ITEM_AXE, [40,5], [], 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[28] = MakeTool(u"Iron shovel", u"Digs up dirts or sands", (107,107,107), [(ITEM_IRON, 5, TYPE_ITEM, (107,107,107))], (ITEM_SHOVEL, [40,5], [], 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[32] = MakeTool(u"Diamond pickaxe", u"Used to pick stones, ores", (80,212,217), [(ITEM_DIAMOND, 5, TYPE_ITEM, (80,212,217))], (ITEM_PICKAXE, [60,1], (BLOCK_IRONORE, BLOCK_SILVERORE, BLOCK_GOLDORE, BLOCK_DIAMONDORE), 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        # returns: 아이템, 체력깎는 정도, 못파는 광물목록
        self.makes[33] = MakeTool(u"Diamond axe", u"Used to cut trees", (80,212,217), [(ITEM_DIAMOND, 5, TYPE_ITEM, (80,212,217))], (ITEM_AXE, [60,1], [], 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[34] = MakeTool(u"Diamond shovel", u"Digs up dirts or sands", (80,212,217), [(ITEM_DIAMOND, 5, TYPE_ITEM, (80,212,217))], (ITEM_SHOVEL, [60,1], [], 0, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[10] = MakeTool(u"Torch(Charcoal)", u"Lights up dark places", (255,255,255), [(ITEM_STICK, 1, TYPE_ITEM, (255,255,255)), (ITEM_CHARCOAL, 1, TYPE_ITEM, (60,60,60))], (ITEM_TORCH, [], [], 1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[11] = MakeTool(u"Torch(Coal)", u"Lights up dark places", (255,255,255), [(ITEM_STICK, 1, TYPE_ITEM, (255,255,255)), (ITEM_COAL, 1, TYPE_ITEM, (60,60,60))], (ITEM_TORCH, [], [], 1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[12] = MakeTool(u"Chest", u"Can hold items and blocks", (255,255,255), [(BLOCK_WOOD, 8, TYPE_BLOCK)], (ITEM_CHEST, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[30] = MakeTool(u"Code", u"Runs python code.\nUsed to launch commands\nor spawn an object\n(Put scripts in scripts directory)", (255,255,255), [(ITEM_GOLD, 4, TYPE_ITEM, (207,207,101)), (ITEM_SILVER, 4, TYPE_ITEM, (201,201,201))], (BLOCK_CODE, [], [], 1, TYPE_BLOCK), self.textRenderer, self.textRendererSmall)
        #self.makes[32] = MakeTool(u"전기선(일자)", u"코드와 기계를\n연결합니다.", (255,255,255), [(ITEM_GOLD, 1, TYPE_ITEM, (207,207,101)), (ITEM_SILVER, 1, TYPE_ITEM, (201,201,201))], (ITEM_LINE, [], [], 10, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        #self.makes[33] = MakeTool(u"전기선(기역자)", u"코드와 기계를\n연결합니다.", (255,255,255), [(ITEM_GOLD, 1, TYPE_ITEM, (207,207,101)), (ITEM_SILVER, 1, TYPE_ITEM, (201,201,201))], (ITEM_LINEL, [], [], 10, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[31] = MakeTool(u"Spawner", u"Spawning spot\n- Machine -", (255,255,255), [(ITEM_GOLD, 4, TYPE_ITEM, (207,207,101)), (ITEM_SILVER, 4, TYPE_ITEM, (201,201,201))], (BLOCK_SPAWNER, [], [], 1, TYPE_BLOCK), self.textRenderer, self.textRendererSmall)
        self.makes[40] = MakeTool(u"Sword", u"A sword\n- Weapon -", (107,107,107), [(ITEM_IRON, 8, TYPE_ITEM, (107,107,107))], (ITEM_SWORD, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[41] = MakeTool(u"Spear", u"A spear\n- Two Handed Weapon -", (107,107,107), [(ITEM_IRON, 16, TYPE_ITEM, (107,107,107))], (ITEM_SPEAR, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[42] = MakeTool(u"Mace", u"A mace\n- Weapon -", (107,107,107), [(ITEM_IRON, 8, TYPE_ITEM, (107,107,107))], (ITEM_MACE, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[43] = MakeTool(u"Brass Knuckle", u"A brass knuckle\n- Weapon -", (107,107,107), [(ITEM_IRON, 8, TYPE_ITEM, (107,107,107))], (ITEM_KNUCKLE, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[44] = MakeTool(u"Shield", u"A shield\n- Shield -", (107,107,107), [(ITEM_IRON, 16, TYPE_ITEM, (107,107,107))], (ITEM_SHIELD, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[45] = MakeTool(u"Helm", u"A Helm\n- Helm -", (107,107,107), [(ITEM_IRON, 8, TYPE_ITEM, (107,107,107))], (ITEM_HELM, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[46] = MakeTool(u"Armor", u"A body armor\n- Armor -", (107,107,107), [(ITEM_IRON, 16, TYPE_ITEM, (107,107,107))], (ITEM_ARMOR, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[47] = MakeTool(u"Gloves", u"A pair of gloves\n- Gloves -", (107,107,107), [(ITEM_IRON, 16, TYPE_ITEM, (107,107,107))], (ITEM_GLOVES, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[48] = MakeTool(u"Boots", u"A pair of boots\n- Boots -", (107,107,107), [(ITEM_IRON, 16, TYPE_ITEM, (107,107,107))], (ITEM_BOOTS, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[50] = MakeTool(u"Silver Ring", u"A silver ring\n- Ring -", (201,201,201), [(ITEM_SILVER, 1, TYPE_ITEM, (201,201,201))], (ITEM_SILVERRING, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[51] = MakeTool(u"Silver Necklace", u"A silver necklace\n- Necklace -", (201,201,201), [(ITEM_SILVER, 1, TYPE_ITEM, (201,201,201))], (ITEM_SILVERNECLACE, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[52] = MakeTool(u"Gold Ring", u"A gold ring\n- Ring -", (207,207,101), [(ITEM_GOLD, 1, TYPE_ITEM, (207,207,101))], (ITEM_GOLDRING, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[53] = MakeTool(u"Gold Necklace", u"A gold necklace\n- Necklace -", (207,207,101), [(ITEM_GOLD, 1, TYPE_ITEM, (207,207,101))], (ITEM_GOLDNECLACE, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[54] = MakeTool(u"Diamond Ring", u"A diamond ring\n- Ring -", (80,212,217), [(ITEM_DIAMOND, 1, TYPE_ITEM, (80,212,217))], (ITEM_DIAMONDRING, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[55] = MakeTool(u"Diamond Necklace", u"A diamond necklace\n- Necklace -", (80,212,217), [(ITEM_DIAMOND, 1, TYPE_ITEM, (80,212,217))], (ITEM_DIAMONDNECLACE, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[56] = MakeTool(u"Blank Scroll", u"Used to make enchant scrolls", (255,255,255), [(BLOCK_WOOD, 1, TYPE_BLOCK)], (ITEM_SCROLL, [], [], 64, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[57] = MakeTool(u"Silver Enchant Scroll", u"Used to enchant an item\n(Use enchant menu to use)", (255,255,255), [(ITEM_SILVER, 1, TYPE_ITEM, (201,201,201)), (ITEM_SCROLL, 1, TYPE_ITEM, (201,201,201))], (ITEM_ENCHANTSCROLL, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[58] = MakeTool(u"Gold Enchant Scroll", u"Used to enchant an item\n(Use enchant menu to use)", (207,207,101), [(ITEM_GOLD, 1, TYPE_ITEM, (207,207,101)), (ITEM_SCROLL, 1, TYPE_ITEM, (201,201,201))], (ITEM_ENCHANTSCROLL, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.makes[59] = MakeTool(u"Diamond\nEnchant Scroll", u"Used to enchant an item\n(Use enchant menu to use)", (80,212,217), [(ITEM_DIAMOND, 1, TYPE_ITEM, (80,212,217)), (ITEM_SCROLL, 1, TYPE_ITEM, (201,201,201))], (ITEM_ENCHANTSCROLL, [], [], -1, TYPE_ITEM), self.textRenderer, self.textRendererSmall)
        self.recipeTextID = self.textRenderer.NewTextObject(u"Recipe:", (0,0,0))

        self.invSlotPos = []
        invX, invY = self.invRealPos
        for y in range(6):
            for x in range(10):
                self.invSlotPos += [(invX+x*30, invY+y*30)]

        self.qbSlotPos = []
        invX, invY = self.qbarRealPos
        y=0
        for x in range(10):
            self.qbSlotPos += [(invX+x*30, invY+y*30)]

        self.makeSlotPos = []
        invX, invY = self.makeRealPos
        for y in range(6):
            for x in range(10):
                self.makeSlotPos += [(invX+x*30, invY+y*30)]

        self.eqSlotPos = []
        """
        무기
        방패
        모자
        몸통
        장갑
        신발
        목걸이
        반지

        0, 200

        26,228
        26,262
        26,296
        26,330

        250,228
        250,262
        250,296
        250,330

        """
        for i in range(4):
            self.eqSlotPos += [(self.makeRealPos[0]+26, self.makeRealPos[1]+28+i*34)]
        for i in range(4):
            self.eqSlotPos += [(self.makeRealPos[0]+250, self.makeRealPos[1]+28+i*34)]

        """
        self.PutItemInInventory(Item(ITEM_GOLD, 64, color = (207,207,101), stackable=True))
        self.PutItemInInventory(Item(ITEM_SILVER, 64, color = (201,201,201), stackable=True))
        self.PutItemInInventory(Block(BLOCK_CODE, 64))
        self.PutItemInInventory(Block(BLOCK_CPU, 64))
        self.PutItemInInventory(Block(BLOCK_ENERGY, 64))
        self.PutItemInInventory(Item(ITEM_IRON, 64, color = (107,107,107), stackable=True))
        self.PutItemInInventory(Item(ITEM_IRON, 64, color = (107,107,107), stackable=True))
        self.PutItemInInventory(Item(ITEM_GOLD, 64, color = (207,207,101), stackable=True))
        self.PutItemInInventory(Item(ITEM_SILVER, 64, color = (201,201,201), stackable=True))
        self.PutItemInInventory(Item(ITEM_DIAMOND, 64, color = (80,212,217), stackable=True))
        """


        # 여기서 텍스쳐를 생성한다.
    def OnIME(self, text):
        pass
    def CanPutItemInInventory(self, item):
        for invItem in self.qbar+self.inventory:
            if not invItem:
                continue
            if invItem.type_ == item.type_ and invItem.count+item.count < invItem.maxLen and invItem.name == item.name and invItem.stackable:
                return True

        idx = 0
        for item_ in self.qbar[:]:
            if item_ == ITEM_NONE:
                return True
            idx += 1

        idx = 0
        for item_ in self.inventory[:]:
            if item_ == ITEM_NONE:
                return True
            idx += 1
        return False

    def PutItemInInventory(self, item):
        for invItem in self.qbar+self.inventory:
            if invItem == ITEM_NONE:
                continue
            if invItem.type_ == item.type_ and invItem.count+item.count < invItem.maxLen and invItem.name == item.name and invItem.stackable:
                invItem.count += item.count
                return True

        idx = 0
        for item_ in self.qbar[:]:
            if item_ == ITEM_NONE:
                self.qbar[idx] = item
                return True
            idx += 1

        idx = 0
        for item_ in self.inventory[:]:
            if item_ == ITEM_NONE:
                self.inventory[idx] = item
                return True
            idx += 1
        return False
    def ShowInventory(self, show):
        # 끌 떄: 아이템을 들고 있는 경우 제자리에 돌려놓음 XXX:
        # 아닌경우 걍 끔
        #
        #
        # 이제 아이템 반으로 나누기
        # 아이템 반 나눈 거 드랍하기
        # 아이템 합치기
        # 아이템 들고있던거 제자리에 못넣을 경우 빈자리에 넣거나 빈공간에 합치기
        if show == False:
            pygame.mouse.set_visible(False)
        else:
            pygame.mouse.set_visible(True)
        if show == False and self.dragging:
            self.dragging = False
            x,y = self.dragPos
            if not self.dragCont[y*10+x]:
                self.dragCont[y*10+x] = self.draggingItem
            else:
                if self.CanPutItemInInventory(self.draggingItem):
                    self.PutItemInInventory(self.draggingItem)
                else:
                    AppSt.DropItem(self.draggingItem)

        self.setInvShown = show

    def Tick(self, t, m, k):
        pass
    def Motion(self, t, m, k):
        self.selectedMakeTool = -1
        if self.invShown:
            if self.toolMode == TM_TOOL:
                idx = 0
                foundIdx = -1
                for pos in self.makeSlotPos:
                    x,y = pos
                    if InRect(x,y,30,30,m.x,m.y):
                        foundIdx = idx
                        break
                    idx += 1

                if foundIdx != -1:
                    x = foundIdx % 10
                    y = (foundIdx - x) / 10
                    self.selectedMakeTool = foundIdx


            idx = 0
            foundIdx = -1
            self.selectedContItem = ITEM_NONE
            for pos in self.invSlotPos:
                x,y = pos
                if InRect(x,y,30,30,m.x,m.y):
                    foundIdx = idx
                    break
                idx += 1
            if foundIdx != -1:
                self.selectedContItem = self.inventory[foundIdx]

            idx = 0
            foundIdx = -1
            for pos in self.qbSlotPos:
                x,y = pos
                if InRect(x,y,30,30,m.x,m.y):
                    foundIdx = idx
                    break
                idx += 1

            if foundIdx != -1:
                self.selectedContItem = self.qbar[foundIdx]

            if self.toolMode == TM_BOX:
                idx = 0
                foundIdx = -1
                for pos in self.makeSlotPos:
                    x,y = pos
                    if InRect(x,y,30,30,m.x,m.y):
                        foundIdx = idx
                        break
                    idx += 1

                if foundIdx != -1:
                    self.selectedContItem = self.selectedBox[foundIdx]
            elif self.toolMode == TM_EQ:
                idx = 0
                foundIdx = -1
                for pos in self.eqSlotPos:
                    x,y = pos
                    if InRect(x,y,30,30,m.x,m.y):
                        foundIdx = idx
                        break
                    idx += 1

                if foundIdx != -1:
                    self.selectedContItem = self.eqs[foundIdx]

    def LDown(self, t, m, k):
        if self.toolMode in [TM_BOX, TM_TOOL, TM_EQ]:
            self.OnDown(t,m,k,False)


    def DoCont(self,x,y,cont, rmb = False):
        if self.dragging:
            #drop or swap
            # real crazy nested if elses
            def Drop():
                self.dragging = False
                cont[y*10+x] = self.draggingItem
                self.draggingItem = None
                self.dragPos = None
                self.dragCont = None
            def Swap():
                if self.draggingItem.type_ == cont[y*10+x].type_ and self.draggingItem.name == cont[y*10+x].name and self.draggingItem.stackable:
                    if self.draggingItem.count+cont[y*10+x].count <= cont[y*10+x].maxLen:
                        cont[y*10+x].count += self.draggingItem.count 
                        self.dragging = False
                    else:
                        temp = self.draggingItem.count + cont[y*10+x].count
                        cont[y*10+x].count = 64
                        self.draggingItem.count = temp-64
                else:
                    self.draggingItem, cont[y*10+x] = cont[y*10+x], self.draggingItem
                # swap or combine

            if cont[y*10+x]:
                if not rmb:
                    Swap()
                else:
                    if self.draggingItem.type_ == cont[y*10+x].type_ and self.draggingItem.name == cont[y*10+x].name and self.draggingItem.stackable:
                        if self.draggingItem.count > 1:
                            half = self.draggingItem.count / 2
                            self.draggingItem.count -= half

                            if half+cont[y*10+x].count <= cont[y*10+x].maxLen:
                                cont[y*10+x].count += half
                            else:
                                temp = half + cont[y*10+x].count
                                cont[y*10+x].count = 64
                                self.draggingItem.count += temp-64
                        else:
                            Swap()
                    else:
                        Swap()
            else:
                if not rmb:
                    Drop()
                else:
                    if self.draggingItem.stackable and self.draggingItem.count > 1:
                        half = self.draggingItem.count / 2
                        self.draggingItem.count -= half
                        if self.draggingItem.name == TYPE_BLOCK:
                            cont[y*10+x] = Block(self.draggingItem.type_, half)
                        elif self.draggingItem.name == TYPE_ITEM:
                            cont[y*10+x] = Item(self.draggingItem.type_, half, color=self.draggingItem.color, stackable=True)
                    else:
                        Drop()
        else:
            # pick
            if cont[y*10+x]:
                def Pick():
                    self.dragging = True
                    self.draggingItem = cont[y*10+x]
                    self.dragPos = (x,y)
                    self.dragCont = cont
                    cont[y*10+x] = ITEM_NONE

                if not rmb:
                    Pick()
                else:
                    if cont[y*10+x].count > 1 and cont[y*10+x].stackable:
                        half = cont[y*10+x].count / 2
                        cont[y*10+x].count -= half
                        self.dragging = True
                        item = cont[y*10+x]
                        if item.name == TYPE_BLOCK:
                            self.draggingItem = Block(cont[y*10+x].type_, half)
                        elif item.name == TYPE_ITEM:
                            self.draggingItem = Item(item.type_, half, color=item.color, stackable=True)

                        self.dragPos = (x,y)
                        self.dragCont = cont
                    else:
                        Pick()

            # start dragging
 
    def RDown(self, t, m, k):
        if self.toolMode in [TM_BOX, TM_TOOL, TM_EQ]:
            self.OnDown(t,m,k,True)


    def DoEquip(self, idx):
        # dragging이 있으면 그걸 입을수있는지 검사
        # 없으면 언이큅
        print idx
        pass
    def OnDown(self, t, m, k, rmb=False):
        if self.invShown:
            idx = 0
            foundIdx = -1
            for pos in self.invSlotPos:
                x,y = pos
                if InRect(x,y,30,30,m.x,m.y):
                    foundIdx = idx
                    break
                idx += 1
            if foundIdx != -1:
                x = foundIdx % 10
                y = (foundIdx - x) / 10
                self.DoCont(x,y, self.inventory, rmb)

            idx = 0
            foundIdx = -1
            for pos in self.qbSlotPos:
                x,y = pos
                if InRect(x,y,30,30,m.x,m.y):
                    foundIdx = idx
                    break
                idx += 1

            if foundIdx != -1:
                x = foundIdx % 10
                y = (foundIdx - x) / 10
                self.DoCont(x,y, self.qbar, rmb)

            if self.toolMode == TM_TOOL:
                idx = 0
                foundIdx = -1
                for pos in self.makeSlotPos:
                    x,y = pos
                    if InRect(x,y,30,30,m.x,m.y):
                        foundIdx = idx
                        break
                    idx += 1

                if foundIdx != -1:
                    x = foundIdx % 10
                    y = (foundIdx - x) / 10
                    self.DoMake(foundIdx)


            elif self.toolMode == TM_BOX:
                idx = 0
                foundIdx = -1
                for pos in self.makeSlotPos:
                    x,y = pos
                    if InRect(x,y,30,30,m.x,m.y):
                        foundIdx = idx
                        break
                    idx += 1

                if foundIdx != -1:
                    x = foundIdx % 10
                    y = (foundIdx - x) / 10
                    self.DoCont(x,y,self.selectedBox, rmb)
            elif self.toolMode == TM_EQ:
                idx = 0
                foundIdx = -1
                for pos in self.eqSlotPos:
                    x,y = pos
                    if InRect(x,y,30,30,m.x,m.y):
                        foundIdx = idx
                        break
                    idx += 1

                if foundIdx != -1:
                    x = foundIdx % 10
                    y = (foundIdx - x) / 10
                    self.DoEquip(foundIdx)


    def GenEntity(self):
        # 음......... 어떤 마법 스킬에 따라서 더 좋은 결과가 나온다.
        # 몬스터도 인챈트 스크롤을 드랍한다. 아이템 대신!
        pass
    def DoMake(self, makeIdx):
        tool = self.makes[makeIdx]

        type_, stats, disallowed, count, name = tool.returns
        if name == TYPE_BLOCK:
            returneditem = Block(type_, count)
        elif name == TYPE_ITEM:
            if type_ == ITEM_ENCHANTSCROLL:

                #인챈트 스크롤 복사하는 아이템이 고급 몬스터에게서 떨어진다. XXX:
                entity = self.GenEntity()
                returneditem = Item(type_, 1, color=tool.color, entity=entity)
            else:
                if count == 0:
                    returneditem = Item(type_, 999, color=tool.color, stats=stats)
                elif count == -1:
                    returneditem = Item(type_, 1, color=tool.color, stats=stats)
                else:
                    returneditem = Item(type_, count, color=tool.color, stackable=True, stats=stats)
        if not self.CanPutItemInInventory(returneditem):
            return

        def Make(nDict):
            for need in tool.needs:
                count = need[1]
                makeList = nDict[need]
                for item, cont in makeList:
                    if item.count > count:
                        item.count -= count
                        count = 0
                    elif item.count == count:
                        count = 0
                        cont[cont.index(item)] = ITEM_NONE
                    else:
                        count -= item.count
                        cont[cont.index(item)] = ITEM_NONE
            self.PutItemInInventory(returneditem)

        needDict = {}
        def DoPass(mList, type_, count, name, cont):
            countNeeds = count
            for item in cont:
                if item and item.type_ == type_ and item.name == name:
                    if item.count >= countNeeds:
                        mList += [(item, cont)]
                        return True, countNeeds
                    else:
                        mList += [(item, cont)]
                        countNeeds -= item.count
            return False, countNeeds

        for need in tool.needs:
            if len(need) == 3:
                type_, count, name = need
            elif len(need) == 4:
                type_, count, name, color = need
            cont = self.inventory
            needDict[need] = []
            found, count = DoPass(needDict[need], type_, count, name, cont)
            if not found:
                cont = self.qbar
                found, count = DoPass(needDict[need], type_, count, name, cont)
                if not found:
                    return

        Make(needDict)




    def LUp(self, t, m, k):
        pass
    def RUp(self, t, m, k):
        pass
    def WDn(self, t, m, k):
        self.selectedItem -= 1
        if self.selectedItem < 0:
            self.selectedItem = 9

    def WUp(self, t, m, k):
        self.selectedItem += 1
        if self.selectedItem > 9:
            self.selectedItem = 0

    def KDown(self, t, m, k):
        if k.pressedKey == K_1:
            self.selectedItem = 0
        if k.pressedKey == K_2:
            self.selectedItem = 1
        if k.pressedKey == K_3:
            self.selectedItem = 2
        if k.pressedKey == K_4:
            self.selectedItem = 3
        if k.pressedKey == K_5:
            self.selectedItem = 4
        if k.pressedKey == K_6:
            self.selectedItem = 5
        if k.pressedKey == K_7:
            self.selectedItem = 6
        if k.pressedKey == K_8:
            self.selectedItem = 7
        if k.pressedKey == K_9:
            self.selectedItem = 8
        if k.pressedKey == K_0:
            self.selectedItem = 9

    def RenderNumber(self, num, x, y):
        count = str(num)
        x = x
        y = y
        for c in count:
            self.textRenderer.RenderText(self.numbers[int(c)], (x, y))
            x += 9

    def Render(self, t, m, k):
        if t - self.prevAreaT >= self.areaDelay:
            self.prevAreaT = t
            if self.invShown:
                self.textRendererArea.Clear()
                #self.testText.Update(self.textRendererArea)
                if self.toolMode == TM_CODE:
                    self.testFile.Update(self.textRendererArea)
                elif self.toolMode == TM_SPAWN:
                    self.testEdit.Update(self.textRendererArea)
        if self.invShown:
            if self.toolMode == TM_CODE:
                self.testFile.Render()
            elif self.toolMode == TM_SPAWN:
                self.testEdit.Render()
            self.textRendererArea.Render()

        glBindTexture(GL_TEXTURE_2D, self.inventex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)

    
        glBegin(GL_QUADS)
        if self.invShown and self.toolMode in [TM_EQ]:
            x,y = self.invPos
            glTexCoord2f(0.0, float(186)/512.0)
            glVertex3f(float(x), -float(y+186), 100.0)

            glTexCoord2f(float(306)/512.0, float(186)/512.0)
            glVertex3f(float(x+306), -float(y+186), 100.0)

            glTexCoord2f(float(306)/512.0, 0.0)
            glVertex3f(float(x+306), -float(y), 100.0)

            glTexCoord2f(0.0, 0.0)
            glVertex3f(x, -float(y), 100.0)

            x,y = self.makePos
            glTexCoord2f(0.0, float(186+200)/512.0)
            glVertex3f(float(x), -float(y+186), 100.0)

            glTexCoord2f(float(306)/512.0, float(186+200)/512.0)
            glVertex3f(float(x+306), -float(y+186), 100.0)

            glTexCoord2f(float(306)/512.0, 0.0+200.0/512.0)
            glVertex3f(float(x+306), -float(y), 100.0)

            glTexCoord2f(0.0, 200.0/512.0)
            glVertex3f(x, -float(y), 100.0)



        if self.invShown and self.toolMode in [TM_BOX, TM_TOOL]:
            x,y = self.invPos
            glTexCoord2f(0.0, float(186)/512.0)
            glVertex3f(float(x), -float(y+186), 100.0)

            glTexCoord2f(float(306)/512.0, float(186)/512.0)
            glVertex3f(float(x+306), -float(y+186), 100.0)

            glTexCoord2f(float(306)/512.0, 0.0)
            glVertex3f(float(x+306), -float(y), 100.0)

            glTexCoord2f(0.0, 0.0)
            glVertex3f(x, -float(y), 100.0)

            x,y = self.makePos
            glTexCoord2f(0.0, float(186)/512.0)
            glVertex3f(float(x), -float(y+186), 100.0)

            glTexCoord2f(float(306)/512.0, float(186)/512.0)
            glVertex3f(float(x+306), -float(y+186), 100.0)

            glTexCoord2f(float(306)/512.0, 0.0)
            glVertex3f(float(x+306), -float(y), 100.0)

            glTexCoord2f(0.0, 0.0)
            glVertex3f(x, -float(y), 100.0)



        x,y = self.qbarPos
        glTexCoord2f(0.0, float(410+38)/512.0)
        glVertex3f(float(x), -float(y+38), 100.0)

        glTexCoord2f(float(308)/512.0, float(410+38)/512.0)
        glVertex3f(float(x+308), -float(y+38), 100.0)

        glTexCoord2f(float(308)/512.0, float(410)/512.0)
        glVertex3f(float(x+308), -float(y), 100.0)

        glTexCoord2f(0.0, float(410)/512.0)
        glVertex3f(x, -float(y), 100.0)

        glEnd()
        if self.invShown and self.toolMode == TM_EQ:
            idx = 0
            for pos in self.eqSlotPos[:4]:
                x,y = pos
                x += 32
                y += 3
                self.textRendererSmall.RenderText(self.eqTexts[idx], (x,y))
                idx += 1
            for pos in self.eqSlotPos[4:]:
                x,y = pos
                x -= 56
                y += 3
                self.textRendererSmall.RenderText(self.eqTexts[idx], (x,y))
                idx += 1



        def RenderItemEq(item, posx, posy, text=True):
            x = posx
            y = posy
            b = item.type_
            if item.name == TYPE_BLOCK:
                glBindTexture(GL_TEXTURE_2D, AppSt.tex)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
                texupx = (BLOCK_TEX_COORDS[b*2*3 + 0]*32.0) / 512.0
                texupy = (BLOCK_TEX_COORDS[b*2*3 + 1]*32.0) / 512.0
                glBegin(GL_QUADS)
                glTexCoord2f(texupx, texupy+float(32)/512.0)
                glVertex3f(float(x), -float(y+30), 100.0)

                glTexCoord2f(texupx+float(32)/512.0, texupy+float(32)/512.0)
                glVertex3f(float(x+30), -float(y+30), 100.0)

                glTexCoord2f(texupx+float(32)/512.0, texupy)
                glVertex3f(float(x+30), -float(y), 100.0)

                glTexCoord2f(texupx, texupy)
                glVertex3f(x, -float(y), 100.0)
                glEnd()
            elif item.name == TYPE_ITEM:
                glBindTexture(GL_TEXTURE_2D, self.tooltex)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                if item.color:
                    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                else:
                    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
                texupx = (TOOL_TEX_COORDS[b*2 + 0]*30.0) / 512.0
                texupy = (TOOL_TEX_COORDS[b*2 + 1]*30.0) / 512.0
                glBegin(GL_QUADS)
                if item.color:
                    glColor4ub(*(item.color+(255,)))
                glTexCoord2f(texupx, texupy+float(30)/512.0)
                glVertex3f(float(x), -float(y+30), 100.0)

                glTexCoord2f(texupx+float(30)/512.0, texupy+float(30)/512.0)
                glVertex3f(float(x+30), -float(y+30), 100.0)

                glTexCoord2f(texupx+float(30)/512.0, texupy)
                glVertex3f(float(x+30), -float(y), 100.0)

                glTexCoord2f(texupx, texupy)
                glVertex3f(x, -float(y), 100.0)
                glEnd()

            """
            texmidx = (BLOCK_TEX_COORDS[b*2*3 + 2]*32.0) / 512.0
            texmidy = (BLOCK_TEX_COORDS[b*2*3 + 3]*32.0) / 512.0
            texbotx = (BLOCK_TEX_COORDS[b*2*3 + 4]*32.0) / 512.0
            texboty = (BLOCK_TEX_COORDS[b*2*3 + 5]*32.0) / 512.0
            """
            if text:
                self.RenderNumber(item.count, x, y)
        def RenderItem(item, idx, posx, posy, text=True):
            x = idx%10
            y = (idx-x)/10
            x*=30
            y*=30
            x += posx
            y += posy
            b = item.type_
            if item.name == TYPE_BLOCK:
                glBindTexture(GL_TEXTURE_2D, AppSt.tex)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
                texupx = (BLOCK_TEX_COORDS[b*2*3 + 0]*32.0) / 512.0
                texupy = (BLOCK_TEX_COORDS[b*2*3 + 1]*32.0) / 512.0
                glBegin(GL_QUADS)
                glTexCoord2f(texupx, texupy+float(32)/512.0)
                glVertex3f(float(x), -float(y+30), 100.0)

                glTexCoord2f(texupx+float(32)/512.0, texupy+float(32)/512.0)
                glVertex3f(float(x+30), -float(y+30), 100.0)

                glTexCoord2f(texupx+float(32)/512.0, texupy)
                glVertex3f(float(x+30), -float(y), 100.0)

                glTexCoord2f(texupx, texupy)
                glVertex3f(x, -float(y), 100.0)
                glEnd()
                w = 29
                h = 29
                y+=1
                glDisable(GL_TEXTURE_2D)

                glLineWidth(1.0)
                glBegin(GL_LINES)
                glColor4f(0.0,0.0,0.0,1.0)
                glVertex3f(float(x), -float(y+h), 100.0)
                glVertex3f(float(x+w), -float(y+h), 100.0)
                
                glVertex3f(float(x+w), -float(y+h), 100.0)
                glVertex3f(float(x+w), -float(y), 100.0)

                glVertex3f(float(x+w), -float(y), 100.0)
                glVertex3f(x, -float(y), 100.0)

                glVertex3f(x, -float(y), 100.0)
                glVertex3f(float(x), -float(y+h), 100.0)
                glEnd()
                glEnable(GL_TEXTURE_2D)

            elif item.name == TYPE_ITEM:
                glBindTexture(GL_TEXTURE_2D, self.tooltex)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                if item.color:
                    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                else:
                    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
                texupx = (TOOL_TEX_COORDS[b*2 + 0]*30.0) / 512.0
                texupy = (TOOL_TEX_COORDS[b*2 + 1]*30.0) / 512.0
                glBegin(GL_QUADS)
                if item.color:
                    glColor4ub(*(item.color+(255,)))
                glTexCoord2f(texupx, texupy+float(30)/512.0)
                glVertex3f(float(x), -float(y+30), 100.0)

                glTexCoord2f(texupx+float(30)/512.0, texupy+float(30)/512.0)
                glVertex3f(float(x+30), -float(y+30), 100.0)

                glTexCoord2f(texupx+float(30)/512.0, texupy)
                glVertex3f(float(x+30), -float(y), 100.0)

                glTexCoord2f(texupx, texupy)
                glVertex3f(x, -float(y), 100.0)
                glEnd()

            """
            texmidx = (BLOCK_TEX_COORDS[b*2*3 + 2]*32.0) / 512.0
            texmidy = (BLOCK_TEX_COORDS[b*2*3 + 3]*32.0) / 512.0
            texbotx = (BLOCK_TEX_COORDS[b*2*3 + 4]*32.0) / 512.0
            texboty = (BLOCK_TEX_COORDS[b*2*3 + 5]*32.0) / 512.0
            """
            if text:
                self.RenderNumber(item.count, x, y)

        if self.invShown:
            if self.toolMode in [TM_EQ]:
                idx = 0
                for item in self.eqs:
                    if not item:
                        pass
                    else:
                        RenderItemEq(item, self.eqSlotPos[idx][0], self.eqSlotPos[idx][1])
                    idx += 1

            if self.toolMode in [TM_BOX, TM_TOOL, TM_EQ]:
                idx = 0
                for item in self.inventory:
                    if not item:
                        idx += 1
                        continue

                    RenderItem(item, idx, self.invRealPos[0], self.invRealPos[1])
                    idx += 1

            if self.toolMode == TM_BOX:
                idx = 0
                for item in self.selectedBox:
                    if not item:
                        idx += 1
                        continue

                    RenderItem(item, idx, self.makeRealPos[0], self.makeRealPos[1])
                    idx += 1
            elif self.toolMode == TM_TOOL:
                idx = 0
                for item in self.makes:
                    if not item:
                        idx += 1
                        continue
                    type_, stats, disallowed, count, name = item.returns
                    if name == TYPE_ITEM:
                        glBindTexture(GL_TEXTURE_2D, self.tooltex)
                        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

                        x = idx%10
                        y = (idx-x)/10
                        x*=30
                        y*=30
                        x += self.makeRealPos[0]
                        y += self.makeRealPos[1]
                        b = item.returns[0]
                        texupx = (TOOL_TEX_COORDS[b*2 + 0]*30.0) / 512.0
                        texupy = (TOOL_TEX_COORDS[b*2 + 1]*30.0) / 512.0
                        """
                        texmidx = (BLOCK_TEX_COORDS[b*2*3 + 2]*32.0) / 512.0
                        texmidy = (BLOCK_TEX_COORDS[b*2*3 + 3]*32.0) / 512.0
                        texbotx = (BLOCK_TEX_COORDS[b*2*3 + 4]*32.0) / 512.0
                        texboty = (BLOCK_TEX_COORDS[b*2*3 + 5]*32.0) / 512.0
                        """

                        # XXX: 재료가 없으면 배경을 빨간색으로 표시
                        """
                        glDisable(GL_TEXTURE_2D)
                        glBegin(GL_QUADS)
                        glColor4ub(200,0,0,200)
                        glVertex3f(float(x), -float(y+30), 100.0)
                        glVertex3f(float(x+30), -float(y+30), 100.0)
                        glVertex3f(float(x+30), -float(y), 100.0)
                        glVertex3f(x, -float(y), 100.0)
                        glEnd()
                        glEnable(GL_TEXTURE_2D)
                        """

                        glBegin(GL_QUADS)
                        glColor4ub(*item.color + (255,))
                        glTexCoord2f(texupx, texupy+float(30)/512.0)
                        glVertex3f(float(x), -float(y+30), 100.0)

                        glTexCoord2f(texupx+float(30)/512.0, texupy+float(30)/512.0)
                        glVertex3f(float(x+30), -float(y+30), 100.0)

                        glTexCoord2f(texupx+float(30)/512.0, texupy)
                        glVertex3f(float(x+30), -float(y), 100.0)

                        glTexCoord2f(texupx, texupy)
                        glVertex3f(x, -float(y), 100.0)
                        glEnd()
                        idx += 1
                    elif name == TYPE_BLOCK:
                        glBindTexture(GL_TEXTURE_2D, AppSt.tex)
                        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)

                        x = idx%10
                        y = (idx-x)/10
                        x*=30
                        y*=30
                        x += self.makeRealPos[0]
                        y += self.makeRealPos[1]
                        b = item.returns[0]
                        texupx = (BLOCK_TEX_COORDS[b*2*3 + 0]*32.0) / 512.0
                        texupy = (BLOCK_TEX_COORDS[b*2*3 + 1]*32.0) / 512.0
                        """
                        texmidx = (BLOCK_TEX_COORDS[b*2*3 + 2]*32.0) / 512.0
                        texmidy = (BLOCK_TEX_COORDS[b*2*3 + 3]*32.0) / 512.0
                        texbotx = (BLOCK_TEX_COORDS[b*2*3 + 4]*32.0) / 512.0
                        texboty = (BLOCK_TEX_COORDS[b*2*3 + 5]*32.0) / 512.0
                        """

                        # XXX: 재료가 없으면 배경을 빨간색으로 표시
                        """
                        glDisable(GL_TEXTURE_2D)
                        glBegin(GL_QUADS)
                        glColor4ub(200,0,0,200)
                        glVertex3f(float(x), -float(y+30), 100.0)
                        glVertex3f(float(x+30), -float(y+30), 100.0)
                        glVertex3f(float(x+30), -float(y), 100.0)
                        glVertex3f(x, -float(y), 100.0)
                        glEnd()
                        glEnable(GL_TEXTURE_2D)
                        """

                        glBegin(GL_QUADS)
                        glColor4ub(*item.color + (255,))
                        glTexCoord2f(texupx, texupy+float(32)/512.0)
                        glVertex3f(float(x), -float(y+30), 100.0)

                        glTexCoord2f(texupx+float(32)/512.0, texupy+float(32)/512.0)
                        glVertex3f(float(x+30), -float(y+30), 100.0)

                        glTexCoord2f(texupx+float(32)/512.0, texupy)
                        glVertex3f(float(x+30), -float(y), 100.0)

                        glTexCoord2f(texupx, texupy)
                        glVertex3f(x, -float(y), 100.0)
                        glEnd()

                        w=29
                        h=29
                        y+=1
                        glDisable(GL_TEXTURE_2D)
                        glLineWidth(1.0)
                        glBegin(GL_LINES)
                        glColor4f(0.0,0.0,0.0,1.0)
                        glVertex3f(float(x), -float(y+h), 100.0)
                        glVertex3f(float(x+w), -float(y+h), 100.0)
                        
                        glVertex3f(float(x+w), -float(y+h), 100.0)
                        glVertex3f(float(x+w), -float(y), 100.0)

                        glVertex3f(float(x+w), -float(y), 100.0)
                        glVertex3f(x, -float(y), 100.0)

                        glVertex3f(x, -float(y), 100.0)
                        glVertex3f(float(x), -float(y+h), 100.0)
                        glEnd()
                        glEnable(GL_TEXTURE_2D)

                        idx += 1

                def RenderItemDesc(item):
                    if not item.entity:
                        return
                    x,y,w,h = 5, 20, 165, 380
                    glDisable(GL_TEXTURE_2D)
                    glBegin(GL_QUADS)
                    glColor4f(1.0,1.0,1.0,0.85)
                    glVertex3f(float(x), -float(y+h), 100.0)
                    glVertex3f(float(x+w), -float(y+h), 100.0)
                    glVertex3f(float(x+w), -float(y), 100.0)
                    glVertex3f(x, -float(y), 100.0)
                    glEnd()

                    glLineWidth(3.0)
                    glBegin(GL_LINES)
                    glColor4f(0.0,0.0,0.0,1.0)
                    glVertex3f(float(x), -float(y+h), 100.0)
                    glVertex3f(float(x+w), -float(y+h), 100.0)
                    
                    glVertex3f(float(x+w), -float(y+h), 100.0)
                    glVertex3f(float(x+w), -float(y), 100.0)

                    glVertex3f(float(x+w), -float(y), 100.0)
                    glVertex3f(x, -float(y), 100.0)

                    glVertex3f(x, -float(y), 100.0)
                    glVertex3f(float(x), -float(y+h), 100.0)
                    glEnd()
                    glEnable(GL_TEXTURE_2D)

                    y = 0
                    tool = self.makes[self.selectedMakeTool]
                    for textid in tool.textidName:
                        self.textRenderer.RenderText(textid, (10, 25+y))
                        y += 20
                    y += 20
                    for textid in tool.textidDesc:
                        self.textRendererSmall.RenderText(textid, (10, 25+y))
                        y += 15
                    y += 20
                    self.textRenderer.RenderText(self.recipeTextID, (10, 25+y))
                    y += 20+25

                    x = 10
                    for need in tool.needs:
                        if len(need) == 3:
                            item, count, textype = need
                            color=(255,255,255)
                        elif len(need) == 4:
                            item, count, textype, color = need
                        if textype == TYPE_BLOCK:
                            glBindTexture(GL_TEXTURE_2D, AppSt.tex)
                            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
                            texupx = (BLOCK_TEX_COORDS[item*2*3 + 0]*32.0) / 512.0
                            texupy = (BLOCK_TEX_COORDS[item*2*3 + 1]*32.0) / 512.0
                            glBegin(GL_QUADS)
                            glTexCoord2f(texupx, texupy+float(32)/512.0)
                            glVertex3f(float(x), -float(y+30), 100.0)

                            glTexCoord2f(texupx+float(32)/512.0, texupy+float(32)/512.0)
                            glVertex3f(float(x+30), -float(y+30), 100.0)

                            glTexCoord2f(texupx+float(32)/512.0, texupy)
                            glVertex3f(float(x+30), -float(y), 100.0)

                            glTexCoord2f(texupx, texupy)
                            glVertex3f(x, -float(y), 100.0)
                            glEnd()
                            self.RenderNumber(count, x, y)
                        elif textype == TYPE_ITEM:
                            glBindTexture(GL_TEXTURE_2D, self.tooltex)
                            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                            texupx = (TOOL_TEX_COORDS[item*2 + 0]*30.0) / 512.0
                            texupy = (TOOL_TEX_COORDS[item*2 + 1]*30.0) / 512.0
                            glBegin(GL_QUADS)
                            glColor3ub(*color)
                            glTexCoord2f(texupx, texupy+float(30)/512.0)
                            glVertex3f(float(x), -float(y+30), 100.0)

                            glTexCoord2f(texupx+float(30)/512.0, texupy+float(30)/512.0)
                            glVertex3f(float(x+30), -float(y+30), 100.0)

                            glTexCoord2f(texupx+float(30)/512.0, texupy)
                            glVertex3f(float(x+30), -float(y), 100.0)

                            glTexCoord2f(texupx, texupy)
                            glVertex3f(x, -float(y), 100.0)
                            glEnd()
                            self.RenderNumber(count, x, y)
                        x += 35
                        if x+35 >= 160:
                            x = 10
                            y += 35


                if self.selectedContItem:
                    if self.selectedContItem.name == "Item":
                        RenderItemDesc(self.selectedContItem)

                if self.selectedMakeTool != -1 and self.makes[self.selectedMakeTool]:
                    x,y,w,h = 5, 20, 165, 380
                    glDisable(GL_TEXTURE_2D)
                    glBegin(GL_QUADS)
                    glColor4f(1.0,1.0,1.0,0.85)
                    glVertex3f(float(x), -float(y+h), 100.0)
                    glVertex3f(float(x+w), -float(y+h), 100.0)
                    glVertex3f(float(x+w), -float(y), 100.0)
                    glVertex3f(x, -float(y), 100.0)
                    glEnd()

                    glLineWidth(3.0)
                    glBegin(GL_LINES)
                    glColor4f(0.0,0.0,0.0,1.0)
                    glVertex3f(float(x), -float(y+h), 100.0)
                    glVertex3f(float(x+w), -float(y+h), 100.0)
                    
                    glVertex3f(float(x+w), -float(y+h), 100.0)
                    glVertex3f(float(x+w), -float(y), 100.0)

                    glVertex3f(float(x+w), -float(y), 100.0)
                    glVertex3f(x, -float(y), 100.0)

                    glVertex3f(x, -float(y), 100.0)
                    glVertex3f(float(x), -float(y+h), 100.0)
                    glEnd()
                    glEnable(GL_TEXTURE_2D)

                    tool = self.makes[self.selectedMakeTool]
                    y = 0
                    for textid in tool.textidName:
                        self.textRenderer.RenderText(textid, (10, 25+y))
                        y += 20
                    y += 20
                    for textid in tool.textidDesc:
                        self.textRendererSmall.RenderText(textid, (10, 25+y))
                        y += 15
                    y += 20
                    self.textRenderer.RenderText(self.recipeTextID, (10, 25+y))
                    y += 20+25

                    x = 10
                    for need in tool.needs:
                        if len(need) == 3:
                            item, count, textype = need
                            color=(255,255,255)
                        elif len(need) == 4:
                            item, count, textype, color = need
                        if textype == TYPE_BLOCK:
                            glBindTexture(GL_TEXTURE_2D, AppSt.tex)
                            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
                            texupx = (BLOCK_TEX_COORDS[item*2*3 + 0]*32.0) / 512.0
                            texupy = (BLOCK_TEX_COORDS[item*2*3 + 1]*32.0) / 512.0
                            glBegin(GL_QUADS)
                            glTexCoord2f(texupx, texupy+float(32)/512.0)
                            glVertex3f(float(x), -float(y+30), 100.0)

                            glTexCoord2f(texupx+float(32)/512.0, texupy+float(32)/512.0)
                            glVertex3f(float(x+30), -float(y+30), 100.0)

                            glTexCoord2f(texupx+float(32)/512.0, texupy)
                            glVertex3f(float(x+30), -float(y), 100.0)

                            glTexCoord2f(texupx, texupy)
                            glVertex3f(x, -float(y), 100.0)
                            glEnd()
                            self.RenderNumber(count, x, y)
                        elif textype == TYPE_ITEM:
                            glBindTexture(GL_TEXTURE_2D, self.tooltex)
                            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                            texupx = (TOOL_TEX_COORDS[item*2 + 0]*30.0) / 512.0
                            texupy = (TOOL_TEX_COORDS[item*2 + 1]*30.0) / 512.0
                            glBegin(GL_QUADS)
                            glColor3ub(*color)
                            glTexCoord2f(texupx, texupy+float(30)/512.0)
                            glVertex3f(float(x), -float(y+30), 100.0)

                            glTexCoord2f(texupx+float(30)/512.0, texupy+float(30)/512.0)
                            glVertex3f(float(x+30), -float(y+30), 100.0)

                            glTexCoord2f(texupx+float(30)/512.0, texupy)
                            glVertex3f(float(x+30), -float(y), 100.0)

                            glTexCoord2f(texupx, texupy)
                            glVertex3f(x, -float(y), 100.0)
                            glEnd()
                            self.RenderNumber(count, x, y)
                        x += 35
                        if x+35 >= 160:
                            x = 10
                            y += 35





        idx = 0
        for item in self.qbar:
            if not item:
                idx += 1
                continue
            RenderItem(item, idx, self.qbarRealPos[0], self.qbarRealPos[1])
            idx += 1

        x = self.selectedItem%10
        y = (self.selectedItem-x)/10
        x*=30
        y*=30
        x += self.qbarRealPos[0]
        y += self.qbarRealPos[1]
        glDisable(GL_TEXTURE_2D)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glColor4f(0.0,0.0,0.0,1.0)
        glVertex3f(float(x), -float(y+30), 100.0)
        glVertex3f(float(x+30), -float(y+30), 100.0)
        
        glVertex3f(float(x+30), -float(y+30), 100.0)
        glVertex3f(float(x+30), -float(y), 100.0)

        glVertex3f(float(x+30), -float(y), 100.0)
        glVertex3f(x, -float(y), 100.0)

        glVertex3f(x, -float(y), 100.0)
        glVertex3f(float(x), -float(y+30), 100.0)
        glEnd()
        glEnable(GL_TEXTURE_2D)

        if self.invShown and self.dragging:
            RenderItem(self.draggingItem, 0, m.x-15,m.y-15)




# 이걸 GLQUAD랑 텍스쳐를 이용하도록 한다.
# 매번 blit할 필요가 없다.
# 글자만 pack 해서 0.5초당 한 번씩 블릿하면 된다!



class CustomIMEModule:
    def __init__(self, printFunc):
        EMgrSt.BindTick(self._OnTick)
        EMgrSt.BindKeyDown(self._OnKeyPressed)
        self.printFunc = printFunc

        self.cmdText = u""

        self.composingText = u""
        self.composing = False

        self.hangulMode = False
        self.chatMode = False

        self.keyPressedWaitedFor = 0
        self.keyRepeatStartWaitedFor = 0
        self.pressedDelay = 50
        self.repeatStartDelay = 250

        self.lastKey = 0
        self.lastText = 0
        self.lastTick = pygame.time.get_ticks()
        

        import hangul
        self.hangulComposer = hangul.HangulComposer()

    def ResetTexts(self):
        self._FinishChatMode()
        self.cmdText = u""
    def SetText(self, text):
        self._FinishChatMode()
        self.cmdText = unicode(text)
    def SetPrintFunc(self, func):
        self.printFunc = func
    def SetActive(self, mode):
        self.chatMode = mode
        if not mode:
            self._FinishChatMode()
        else:
            pass

    def _ToggleHangulMode(self):
        self.hangulMode = not self.hangulMode

    def _FinishChatMode(self):
        self._FinishHangulComposing()

    def _OnTick(self, tick, lastMouseState, lastKeyState):
        tick2 = tick - self.lastTick
        self.lastTick = tick
        def RepeatKeyEvent():
            if lastKeyState.GetPressedKey():
                # check if it's time to start to repeat
                if self.keyRepeatStartWaitedFor > self.repeatStartDelay and \
                        self.keyPressedWaitedFor > self.pressedDelay: # check if last repeat waiting is over
                    self.keyPressedWaitedFor = 0
                    if self.lastKey != K_RETURN:
                        self._ProcessKeyPressed(self.lastKey, self.lastText)
                self.keyPressedWaitedFor += tick2
                self.keyRepeatStartWaitedFor += tick2

        if self.chatMode:
            RepeatKeyEvent()

    def _OnKeyPressed(self, tick, m, k):
        if self.chatMode:
            def ResetRepeatKeyEvent():
                self.keyPressedWaitedFor = 0
                self.keyRepeatStartWaitedFor = 0
            ResetRepeatKeyEvent()
            self._ProcessKeyPressed(k.pressedKey, k.pressedChar)

    def _ProcessKeyPressed(self, key, text):
        self.lastKey = key
        self.lastText = text

        if key == K_RALT:
            self._ToggleHangulMode()

        elif key == K_BACKSPACE:
            if self.hangulComposer.iscomposing():
                self._DoHangulBackspace()
            else:
                if self.cmdText:
                    self.cmdText = self.cmdText[:-1]
            self._PrintCmd(self.cmdText + self.composingText)

        else:
            self._ProcessChar(text)
            self._PrintCmd(self.cmdText + self.composingText)

    def _DoHangulBackspace(self):
        bs = self.hangulComposer.backspace()
        if bs:
            uni, finished, finishedUni = bs
            if uni:
                self._StartHangulComposing(uni)
            else:
                self._FinishHangulComposing()
        else:
            self._FinishHangulComposing()

    def _StartHangulComposing(self, composingText):
        self.composing = True
        self.composingText = composingText
    def _FinishHangulComposing(self):
        self.hangulComposer.finish()
        if self.composing:
            self.cmdText += self.composingText
            self.composing = False
            self.composingText = u''

    def _ProcessChar(self, char):
        if len(self.cmdText) > 50:
            return
        alphabets = SpecialStrings.GetAlphabets()
        numerics = SpecialStrings.GetNumerics()
        specials = SpecialStrings.GetSpecials()
        #char = chr(char)

        if self.hangulMode and char in alphabets:
            uni, finished, finishedUni = self.hangulComposer.feed(char) # XXX: feel exotic to use huh?
            if finished:
                self.cmdText += finishedUni
                self._StartHangulComposing(uni[len(finishedUni):])
            else:
                self._StartHangulComposing(uni)

        elif char in numerics + alphabets + specials:
            self._FinishHangulComposing()
            self.cmdText += char
        else:
            self._FinishHangulComposing()

    def _PrintCmd(self, text):
        self.printFunc(text)



EMgrSt = None
class EventManager(object):
    def __init__(self):
        global EMgrSt
        EMgrSt = self
        self.lastMouseState = MouseState()
        self.lastKeyState = KeyState()
        self.bindMDown = []
        self.bindMUp = []
        self.bindMotion = []
        self.bindTick = []

        self.ldown = []
        self.rdown = []
        self.mdown = []
        self.lup = []
        self.rup = []
        self.mup = []
        self.wup = []
        self.wdn = []
        self.bindLPressing = []
        self.bindMPressing = []
        self.bindRPressing = []
        self.kdown = []
        self.kup = []
        self.tick = 0

        self.prevEvent = 0
        self.eventDelay = 50

    def BindWUp(self, func):
        self.wup += [func]
    def BindWDn(self, func):
        self.wdn += [func]
    def BindLPressing(self, func):
        self.bindLPressing += [func]
    def BindMPressing(self, func):
        self.bindMPressing += [func]
    def BindRPressing(self, func):
        self.bindRPressing += [func]
    def BindLDown(self, func):
        self.ldown += [func]
    def BindLUp(self, func):
        self.lup += [func]
    def BindRDown(self, func):
        self.rdown += [func]
    def BindRUp(self, func):
        self.rup += [func]
    def BindMUp(self, func):
        self.bindMUp += [func]
    def BindMDown(self, func):
        self.bindMDown += [func]
    def BindMotion(self, func):
        self.bindMotion += [func]
    def BindTick(self, func):
        self.bindTick += [func]
    def BindKeyUp(self, func):
        self.kup += [func]
    def BindKeyDown(self, func):
        self.kdown += [func]

    def Tick(self):
        self.tick = pygame.time.get_ticks()
        self.tick = pygame.time.get_ticks()
        self.lastMouseState.OnTick(self.tick)
        self.tick = pygame.time.get_ticks()
        self.lastKeyState.OnTick(self.tick)
        for func in self.bindTick:
            self.tick = pygame.time.get_ticks()
            func(self.tick, self.lastMouseState, self.lastKeyState)


        pressedButtons = self.lastMouseState.GetPressedButtons()
        for button in pressedButtons.iterkeys():
            if button == LMB:
                for func in self.bindLPressing:
                    self.tick = pygame.time.get_ticks()
                    func(self.tick, self.lastMouseState, self.lastKeyState)
            if button == MMB:
                for func in self.bindMPressing:
                    self.tick = pygame.time.get_ticks()
                    func(self.tick, self.lastMouseState, self.lastKeyState)
            if button == RMB:
                for func in self.bindRPressing:
                    self.tick = pygame.time.get_ticks()
                    func(self.tick, self.lastMouseState, self.lastKeyState)

            

        if self.tick - self.prevEvent > self.eventDelay:
            self.prevEvent = self.tick

    def Event(self, e):
        if e.type is MOUSEBUTTONDOWN:
            x,y = e.pos
            self.lastMouseState.OnMousePressed(x,y,SW,SH,e.button)
            for func in self.bindMDown:
                self.tick = pygame.time.get_ticks()
                func(self.tick, self.lastMouseState, self.lastKeyState)

            dic = {LMB: self.ldown, MMB: self.mdown, RMB: self.rdown, WUP: self.wup, WDN: self.wdn}
            for button in dic:
                if e.button == button:
                    for func in dic[button]:
                        self.tick = pygame.time.get_ticks()
                        func(self.tick, self.lastMouseState, self.lastKeyState)
                
        elif e.type is MOUSEBUTTONUP:
            x,y = e.pos
            self.lastMouseState.OnMouseReleased(x,y,SW,SH, e.button)
            for func in self.bindMUp:
                self.tick = pygame.time.get_ticks()
                func(self.tick, self.lastMouseState, self.lastKeyState)

            dic = {LMB: self.lup, MMB: self.mup, RMB: self.rup}
            for button in dic:
                if e.button == button:
                    for func in dic[button]:
                        self.tick = pygame.time.get_ticks()
                        func(self.tick, self.lastMouseState, self.lastKeyState)
        elif e.type is MOUSEMOTION:
            x,y = e.pos
            x2,y2 = e.rel
            self.lastMouseState.OnMouseMoved(x,y,SW,SH,x2,y2,0)
            for func in self.bindMotion:
                self.tick = pygame.time.get_ticks()
                func(self.tick, self.lastMouseState, self.lastKeyState)

        elif e.type is KEYDOWN:
            self.lastKeyState.OnKeyPressed(e.key, e.unicode, e.mod)
            for func in self.kdown:
                self.tick = pygame.time.get_ticks()
                func(self.tick, self.lastMouseState, self.lastKeyState)
        elif e.type is KEYUP:
            self.lastKeyState.OnKeyReleased()
            for func in self.kup:
                self.tick = pygame.time.get_ticks()
                func(self.tick, self.lastMouseState, self.lastKeyState)
            """
    KEYDOWN	     unicode, key, mod
    KEYUP	     key, mod
            """

def emptyfunc(pos):
    pass
class MouseEventHandler(object):
    def __init__(self, rect):
        self.rect = rect
        self.ldown = emptyfunc
        self.rdown = emptyfunc

    def BindLDown(self, func):
        self.ldown = func
    def BindRDown(self, func):
        self.rdown = func

    def Event(self, e):
        self.OnLDown(e)
        self.OnRDown(e)

    def OnRDown(self, e):
        if e.type is MOUSEBUTTONDOWN:
            if e.button == RMB:
                x, y = e.pos
                x2,y2,w,h = self.rect
                if InRect(x2,y2,w,h,x,y):
                    self.rdown(e.pos)

    def OnLDown(self, e):
        if e.type is MOUSEBUTTONDOWN:
            if e.button == LMB:
                x, y = e.pos
                x2,y2,w,h = self.rect
                if InRect(x2,y2,w,h,x,y):
                    self.ldown(e.pos)


class MouseState(object):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.relX = 0
        self.relY = 0
        self.relZ = 0
        self.pressedButtons = {}

    def OnMouseMoved(self, x, y, w, h, relX, relY, relZ):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.relX = relX
        self.relY = relY
        self.relZ = relZ
    def OnMousePressed(self, x, y, w, h, id):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.pressedButtons[id] = 0
    def OnMouseReleased(self, x, y, w, h, id):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        try:
            del self.pressedButtons[id]
        except:
            pass
    def UpdateWithMouseState(self, mouseState):
        self.x, self.y, self.w, self.h = mouseState.GetValues()
        self.relX, self.relY = self.GetRelativeMovements()
        for key in mouseState.GetPressedButtons().iterkeys():
            self.pressedButtons[key] = mouseState.GetPressedButtons()[key]
    def OnTick(self, time):
        for key in self.pressedButtons.iterkeys():
            self.pressedButtons[key] += time

    def GetValues(self):
        return self.x, self.y, self.w, self.h
    def GetRelativeMovements(self):
        return self.relX, self.relY
    def GetWheelMovement(self):
        return self.relZ
    def GetPressedButtons(self):
        return self.pressedButtons
    def _GetScreenVector(self, x, y, w, h):
        if w and h:
            mx = float(x) - float(w)/2.0
            my = float(y) - float(h)/2.0
            vectorX, vectorY = mx/(float(w)/2.0), -my/(float(h)/2.0)
            return vectorX, vectorY
        else:
            return 0, 0
    def GetScreenVector(self):
        return self._GetScreenVector(*self.GetValues())

    def GetScreenVectorDegree(self):
        vector = self.GetScreenVector()
        return Vector2ToAngle(*vector)

def DegreeTo8WayDirection(degree):
    degrees = [((360 / 8)*i)-360/16 for i in range(9)]
    degrees[0] += 360
    if (0 <= degree < degrees[1]) or (degrees[0] <= degree < 360) or (degree == 360):
        return "e"

    directions = ["ne", "n", "nw", "w", "sw", "s", "se"]
    
    idx = 0
    for degIdx in range(len(degrees[1:])):
        deg1 = degrees[1:][idx]
        deg2 = degrees[1:][idx+1]
        if deg1 <= degree < deg2:
            return directions[idx]
        idx += 1
"""

          +
          +
          +
          +
          +
----------------------
          +
          +
          +
          +
          +
"""

def Vector2ToAngle(x, y):
    vecOrg = Vector2(1.0, 0.0)
    vecPos = Vector2(x, y)
    vecPos = vecPos.normalised()
    dotted = vecOrg.dotProduct(vecPos)
    if dotted == 0.0:
        dotted = 0.0001
    convert = 360.0/(2*math.pi)

    angle = math.acos(dotted)*convert
    if y < 0:
        angle = -angle
    angle %= 360
    return angle

class KeyState(object):
    def __init__(self):
        self.pressedKey = None
        self.pressedChar = None
        self.pressedMod = None
        self.timePressedFor = None

    def OnKeyPressed(self, key, text, mod):
        self.pressedKey = key
        self.pressedChar = text
        self.pressedMod = mod
        self.timePressedFor = 0
    def OnTick(self, time):
        if self.timePressedFor:
            self.timePressedFor += time
    def OnKeyReleased(self):
        self.pressedKey = None
        self.pressedChar = None
        self.pressedMod = None
        self.timePressedFor = None

    def GetPressedKey(self):
        return self.pressedKey
    def GetPressedTime(self):
        return self.timePressedFor

class Vector2(object):
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    def normalised(self):
        l = self.length()
        if l == 0.0:
            l = 1
        return Vector2(self.x / l, self.y / l)
    def __neg__(self):
        return Vector2(-self.x, -self.y)
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    def __radd__(self, other):
        return self.__add__(other)
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    def __rsub__(self, other):
        return self.__sub__(other)
    def __mul__(self, other):
        if type(other) in (int, float):
            return Vector2(self.x * other, self.y * other)
        else: # dot product
            return self.x * other.x + self.y * other.y
    def __rmul__(self, other):
        return self.__mul__(other)
    def __div__(self, other):
        return Vector2(self.x / other, self.y / other)
    def dotProduct(self, other):
        return self.x * other.x + self.y * other.y

def tangent(a, b):
    return (a-b)/2.0
def CatmullRomSpline(p0, p1, p2, p3, resolution=0.1):

    m0 = tangent(p1, p0)
    m1 = tangent(p2, p0)
    m2 = tangent(p3, p1)
    m3 = tangent(p3, p2)
    t = 0.0
    a = []
    b = []
    c = []
    while t < 1.0:
        t_2 = t * t
        _1_t = 1 - t
        _2t = 2 * t
        h00 =  (1 + _2t) * (_1_t) * (_1_t)
        h10 =  t  * (_1_t) * (_1_t)
        h01 =  t_2 * (3 - _2t)
        h11 =  t_2 * (t - 1)

        result = Vector2(0.0,0.0)
        result.x = h00 * p0.x + h10 * m0.x + h01 * p1.x + h11 * m1.x
        result.y = h00 * p0.y + h10 * m0.y + h01 * p1.y + h11 * m1.y
        a.append(result)
        result = Vector2(0.0,0.0)
        result.x = h00 * p1.x + h10 * m1.x + h01 * p2.x + h11 * m2.x
        result.y = h00 * p1.y + h10 * m1.y + h01 * p2.y + h11 * m2.y
        b.append(result)
        result = Vector2(0.0,0.0)
        result.x = h00 * p2.x + h10 * m2.x + h01 * p3.x + h11 * m3.x
        result.y = h00 * p2.y + h10 * m2.y + h01 * p3.y + h11 * m3.y
        c.append(result)
        t+=resolution
    out = []

    for point in b:
        out.append(point)
    return out

def IsClockwise(x0,x1,x2,y0,y1,y2):
    return ((x1-x0)*(y2-y0) - (x2-x0)*(y1-y0)) < 0

def MbyM44(m, n):
    m[0],m[4],m[8],m[12]
    m[1],m[5],m[9],m[13]
    m[2],m[6],m[10],m[14]
    m[3],m[7],m[11],m[15]

    n[0],n[4],n[8],n[12]
    n[1],n[5],n[9],n[13]
    n[2],n[6],n[10],n[14]
    n[3],n[7],n[11],n[15]

    l = [0 for i in range(16)]
    l[0] = m[0]*n[0] + m[1]*n[4] + m[2]*n[8] + m[3]*n[12]
    l[1] = m[0]*n[1] + m[1]*n[5] + m[2]*n[9] + m[3]*n[13]
    l[2] = m[0]*n[2] + m[1]*n[6] + m[2]*n[10] + m[3]*n[14]
    l[3] = m[0]*n[3] + m[1]*n[7] + m[2]*n[11] + m[3]*n[15]

    l[4] = m[4]*n[0] + m[5]*n[4] + m[6]*n[8] + m[7]*n[12]
    l[5] = m[4]*n[1] + m[5]*n[5] + m[6]*n[9] + m[7]*n[13]
    l[6] = m[4]*n[2] + m[5]*n[6] + m[6]*n[10] + m[7]*n[14]
    l[7] = m[4]*n[3] + m[5]*n[7] + m[6]*n[11] + m[7]*n[15]

    l[8] = m[8]*n[0] + m[9]*n[4] + m[10]*n[8] + m[11]*n[12]
    l[9] = m[8]*n[1] + m[9]*n[5] + m[10]*n[9] + m[11]*n[13]
    l[10] = m[8]*n[2] + m[9]*n[6] + m[10]*n[10] + m[11]*n[14]
    l[11] = m[8]*n[3] + m[9]*n[7] + m[10]*n[11] + m[11]*n[15]

    l[12] = m[12]*n[0] + m[13]*n[4] + m[14]*n[8] + m[15]*n[12]
    l[13] = m[12]*n[1] + m[13]*n[5] + m[14]*n[9] + m[15]*n[13]
    l[14] = m[12]*n[2] + m[13]*n[6] + m[14]*n[10] + m[15]*n[14]
    l[15] = m[12]*n[3] + m[13]*n[7] + m[14]*n[11] + m[15]*n[15]
    return l

def ViewingMatrix():
    projection = glGetDoublev( GL_PROJECTION_MATRIX)
    model = glGetDoublev( GL_MODELVIEW_MATRIX )
    # hmm, this will likely fail on 64-bit platforms :(
    if projection is None or model is None:
        if projection:
            return projection
        if model:
            return model
        return None
    else:
        m = model
        p = projection
        return numpy.dot(m,p)

def GetFrustum(matrix):
    frustum = numpy.zeros( (6, 4), 'd' )
    clip = numpy.ravel(matrix)
    # right
    frustum[0][0] = clip[ 3] - clip[ 0]
    frustum[0][1] = clip[ 7] - clip[ 4]
    frustum[0][2] = clip[11] - clip[ 8]
    frustum[0][3] = clip[15] - clip[12]
    # left
    frustum[1][0] = clip[ 3] + clip[ 0]
    frustum[1][1] = clip[ 7] + clip[ 4]
    frustum[1][2] = clip[11] + clip[ 8]
    frustum[1][3] = clip[15] + clip[12]
    # bottom
    frustum[2][0] = clip[ 3] + clip[ 1]
    frustum[2][1] = clip[ 7] + clip[ 5]
    frustum[2][2] = clip[11] + clip[ 9]
    frustum[2][3] = clip[15] + clip[13]
    # top
    frustum[3][0] = clip[ 3] - clip[ 1]
    frustum[3][1] = clip[ 7] - clip[ 5]
    frustum[3][2] = clip[11] - clip[ 9]
    frustum[3][3] = clip[15] - clip[13]
    # far
    frustum[4][0] = clip[ 3] - clip[ 2]
    frustum[4][1] = clip[ 7] - clip[ 6]
    frustum[4][2] = clip[11] - clip[10]
    frustum[4][3] = clip[15] - clip[14]
    # near
    frustum[5][0] = clip[ 3] + clip[ 2]
    frustum[5][1] = clip[ 7] + clip[ 6]
    frustum[5][2] = clip[11] + clip[10]
    frustum[5][3] = clip[15] + clip[14]
    return frustum
def NormalizeFrustum(frustum):
    magnitude = numpy.sqrt( 
        frustum[:,0] * frustum[:,0] + 
        frustum[:,1] * frustum[:,1] + 
        frustum[:,2] * frustum[:,2] 
    )
    # eliminate any planes which have 0-length vectors,
    # those planes can't be used for excluding anything anyway...
    frustum = numpy.compress( magnitude,frustum,0 )
    magnitude = numpy.compress( magnitude, magnitude,0 )
    magnitude = numpy.reshape(magnitude.astype('d'), (len(frustum),1))
    return frustum/magnitude


"""
class Frustum (node.Node):
    ""Holder for frustum specification for intersection tests

    Note:
        the Frustum can include an arbitrary number of
        clipping planes, though the most common usage
        is to define 6 clipping planes from the OpenGL
        model-view matrices.
    ""
    ARRAY_TYPE = 'd'
    planes = fieldtypes.MFVec4f( 'planes', 1, [])
    normalized = fieldtypes.SFBool( 'normalized', 0, 1)
    def fromViewingMatrix(cls, matrix= None, normalize=1):
        ""Extract and calculate frustum clipping planes from OpenGL

        The default initializer allows you to create
        Frustum objects with arbitrary clipping planes,
        while this alternate initializer provides
        automatic clipping-plane extraction from the
        model-view matrix.

        matrix -- the combined model-view matrix
        normalize -- whether to normalize the plane equations
            to allow for sphere bounding-volumes and use of
            distance equations for LOD-style operations.
        ""
        if matrix is None:
            matrix = viewingMatrix( )
        clip = ravel(matrix)
        frustum = zeros( (6, 4), cls.ARRAY_TYPE )
        # right
        frustum[0][0] = clip[ 3] - clip[ 0]
        frustum[0][1] = clip[ 7] - clip[ 4]
        frustum[0][2] = clip[11] - clip[ 8]
        frustum[0][3] = clip[15] - clip[12]
        # left
        frustum[1][0] = clip[ 3] + clip[ 0]
        frustum[1][1] = clip[ 7] + clip[ 4]
        frustum[1][2] = clip[11] + clip[ 8]
        frustum[1][3] = clip[15] + clip[12]
        # bottom
        frustum[2][0] = clip[ 3] + clip[ 1]
        frustum[2][1] = clip[ 7] + clip[ 5]
        frustum[2][2] = clip[11] + clip[ 9]
        frustum[2][3] = clip[15] + clip[13]
        # top
        frustum[3][0] = clip[ 3] - clip[ 1]
        frustum[3][1] = clip[ 7] - clip[ 5]
        frustum[3][2] = clip[11] - clip[ 9]
        frustum[3][3] = clip[15] - clip[13]
        # far
        frustum[4][0] = clip[ 3] - clip[ 2]
        frustum[4][1] = clip[ 7] - clip[ 6]
        frustum[4][2] = clip[11] - clip[10]
        frustum[4][3] = clip[15] - clip[14]
        # near
        frustum[5][0] = clip[ 3] + clip[ 2]
        frustum[5][1] = clip[ 7] + clip[ 6]
        frustum[5][2] = clip[11] + clip[10]
        frustum[5][3] = clip[15] + clip[14]
        if normalize:
            frustum = cls.normalize( frustum )
        return cls( planes = frustum, normalized = normalize )
    fromViewingMatrix = classmethod(fromViewingMatrix)
    def normalize(cls, frustum):
        ""Normalize clipping plane equations""
        magnitude = sqrt( 
            frustum[:,0] * frustum[:,0] + 
            frustum[:,1] * frustum[:,1] + 
            frustum[:,2] * frustum[:,2] 
        )
        # eliminate any planes which have 0-length vectors,
        # those planes can't be used for excluding anything anyway...
        frustum = compress( magnitude,frustum,0 )
        magnitude = compress( magnitude, magnitude,0 )
        magnitude=reshape(magnitude.astype(cls.ARRAY_TYPE), (len(frustum),1))
        return frustum/magnitude
    normalize = classmethod(normalize)
"""

def resize(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, float(width)/height, .1, 1000.)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def init():
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glClearColor(1.0, 1.0, 1.0, 0.0)
    

def glpPerspective(fovy, aspect, zNear, zFar):
    top = math.tan(fovy * math.pi / 360.0) * zNear
    bottom = -top
    left = aspect * bottom
    right = aspect * top
    glFrustum(float(left), float(right), float(bottom), float(top), float(zNear), float(zFar))

def GUIDrawMode():
    glDisable(GL_CULL_FACE)
    glDisable(GL_DEPTH_TEST)
    #glViewport(0, 0, SW, SH)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, float(SW), -float(SH), 0.0, -1000.0, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

G_FAR = 20.0
def GameDrawMode():
    glEnable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    h = SH
    if SH == 0: h = 1
    aspect = float(SW) / float(h)
    fov = 90.0
    near = 0.1 # 이게 너무 작으면 Z버퍼가 정확도가 낮으면 글픽 깨짐
    far = G_FAR

    #glViewport(0, 0, SW, SH)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glpPerspective(90.0, aspect, near, far)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

class Quaternion:
    def __init__(self, x = 0, y = 0, z = 0, w = 1):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def Length(self):
        return sqrtf(self.x**2+self.y**2+self.z**2+self.w**2)

    def Normalized(self):
        len = self.Length()
        try:
            factor = 1.0/len
            x = self.x * factor
            y = self.y * factor
            z = self.z * factor
            w = self.w * factor
        except ZeroDivisionError:
            x = self.x
            y = self.y
            z = self.z
            w = self.w
        return Quaternion(x,y,z,w)


    def CreateFromAxisAngle(self, x, y, z, degrees):
        angle = (degrees / 180.0) * math.pi
        result = math.sin( angle / 2.0 )
        self.w = math.cos( angle / 2.0 )
        self.x = (x * result)
        self.y = (y * result)
        self.z = (z * result)

    def CreateMatrix(self):
        pMatrix = [0 for i in range(16)]
	
	# First row
	pMatrix[ 0] = 1.0 - 2.0 * ( self.y * self.y + self.z * self.z )
	pMatrix[ 1] = 2.0 * (self.x * self.y + self.z * self.w)
	pMatrix[ 2] = 2.0 * (self.x * self.z - self.y * self.w)
	pMatrix[ 3] = 0.0
	
	# Second row
	pMatrix[ 4] = 2.0 * ( self.x * self.y - self.z * self.w )
	pMatrix[ 5] = 1.0 - 2.0 * ( self.x * self.x + self.z * self.z )
	pMatrix[ 6] = 2.0 * (self.z * self.y + self.x * self.w )
	pMatrix[ 7] = 0.0

	# Third row
	pMatrix[ 8] = 2.0 * ( self.x * self.z + self.y * self.w )
	pMatrix[ 9] = 2.0 * ( self.y * self.z - self.x * self.w )
	pMatrix[10] = 1.0 - 2.0 * ( self.x * self.x + self.y * self.y )
	pMatrix[11] = 0.0

	# Fourth row
	pMatrix[12] = 0
	pMatrix[13] = 0
	pMatrix[14] = 0
	pMatrix[15] = 1.0
        return pMatrix


    def Conjugate(self):
        x = -self.x
        y = -self.y
        z = -self.z
        w = self.w
        return Quaternion(x,y,z,w)

    def __mul__(self, quat):
        x = self.w*quat.x + self.x*quat.w + self.y*quat.z - self.z*quat.y;
        y = self.w*quat.y - self.x*quat.z + self.y*quat.w + self.z*quat.x;
        z = self.w*quat.z + self.x*quat.y - self.y*quat.x + self.z*quat.w;
        w = self.w*quat.w - self.x*quat.x - self.y*quat.y - self.z*quat.z;
        return Quaternion(x,y,z,w)

    def __repr__(self):
        return str([self.w, [self.x,self.y,self.z]])
    
    def Dot(self, q):
        q = q.Normalized()
        self = self.Normalized()
        return self.x*q.x + self.y*q.y + self.z*q.z + self.w*q.w

    def Slerp(self, q, t):
        import math
        if t <= 0.0:
            return Quaternion(self.x, self.y, self.z, self.w)
        elif t >= 1.0:
            return Quaternion(q.x, q.y, q.z, q.w)

        cosOmega = self.Dot(q)
        if cosOmega < 0:
            cosOmega = -cosOmega
            q2 = Quaternion(-q.x, -q.y, -q.z, -q.w)
        else:
            q2 = Quaternion(q.x, q.y, q.z, q.w)
        
        if 1.0 - cosOmega > 0.00001:
            omega = math.acos(cosOmega)
            sinOmega = sin(omega)
            oneOverSinOmega = 1.0 / sinOmega

            k0 = sin((1.0 - t) * omega) / sinOmega
            k1 = sin(t * omega) / sinOmega
        else:
            k0 = 1.0 - t
            k1 = t
        return Quaternion(
                (k0 * self.x) + (k1 * q2.x),
                (k0 * self.y) + (k1 * q2.y),
                (k0 * self.z) + (k1 * q2.z),
                (k0 * self.w) + (k1 * q2.w))

class Vector:
    def __init__(self, x = 0, y = 0, z = 0, w=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def Length(self):
        import math
        return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z)

    def NormalizeByW(self):
        x,y,z,w = self.x,self.y,self.z,self.w
        w = float(w)
        if w == 0.0:
            w = 0.000001
        x /= w
        y /= w
        z /= w
        w = 1.0
        return Vector(x,y,z,w)

    def Normalized(self):
        try:
            newV = self.NormalizeByW()
            factor = 1.0/newV.Length()
            return newV.MultScalar(factor)
        except ZeroDivisionError:
            return Vector(self.x, self.y, self.z, self.w)

    def Cross(self, vector):
        newV = self.NormalizeByW()
        vector = vector.NormalizeByW()
        return Vector(*cross(newV.x,newV.y,newV.z,vector.x,vector.y,vector.z))

    def Dot(self, vector):
        newV = self.NormalizeByW()
        newV = newV.Normalized()
        vector = vector.NormalizeByW()
        vector = vector.Normalized()
        return newV.x*vector.x+newV.y*vector.y+newV.z*vector.z

    def __add__(self, vec):
        newV = self.NormalizeByW()
        vec = vec.NormalizeByW()
        a,b,c = newV.x,newV.y,newV.z
        x,y,z = vec.x,vec.y,vec.z
        return Vector(a+x,b+y,c+z)

    def __sub__(self, vec):
        newV = self.NormalizeByW()
        vec = vec.NormalizeByW()
        a,b,c = newV.x,newV.y,newV.z
        x,y,z = vec.x,vec.y,vec.z
        return Vector(a-x,b-y,c-z)

    def MultScalar(self, scalar):
        newV = self.NormalizeByW()
        return Vector(newV.x*scalar, newV.y*scalar, newV.z*scalar)
    def DivScalar(self, scalar):
        newV = self.NormalizeByW()
        return Vector(newV.x/scalar, newV.y/scalar, newV.z/scalar)
    def __repr__(self):
        return str([self.x, self.y, self.z, self.w])
    
    def MultMatrix(self, mat):
        tempVec = Vector()
        tempVec.x = self.x*mat[0] + self.y*mat[1] + self.z*mat[2] + self.w*mat[3]
        tempVec.y = self.x*mat[4] + self.y*mat[5] + self.z*mat[6] + self.w*mat[7]
        tempVec.z = self.x*mat[8] + self.y*mat[9] + self.z*mat[10] + self.w*mat[11]
        tempVec.w = self.x*mat[12] + self.y*mat[13] + self.z*mat[14] + self.w*mat[15]
        return tempVec




    
def glpLookAt(eye, center, up):
    m = [0.0 for i in range(16)]
    forward = center-eye
    forward = forward.Normalized()

    side = forward.Cross(up)
    side = side.Normalized()
    
    up = side.Cross(forward)

    m_ = [side.x, up.x, -forward.x, 0,
        side.y, up.y, -forward.y, 0,
        side.z, up.z, -forward.z, 0,
        0, 0, 0, 1]

    for i in range(16):
        m[i] = float(m_[i])

    glMultMatrixf(m)
    glTranslatef(-eye.x, -eye.y, -eye.z)

class Camera:
    def __init__(self):
        """
        self.view = Vector(0, 0, 1.0).Normalized()
        self.rotX = 0
        self.rotY = ((math.pi/2)-0.1)
        self.posz = -3.0
        self.posx = 0
        self.posy = 0
        """
        self.qPitch = Quaternion()
        self.qHeading = Quaternion()
        self.pitchDegrees = 0.0
        self.headingDegrees = 0.0
        self.directionVector = Vector()
        self.forwardVelocity = 1.0
        self.pos = Vector(0.0, 0.0, 0.0)

    def RotateVert(self, vert, angle, axis):
        axis = axis.Normalized()
        V = Quaternion(vert.x, vert.y, vert.z, 0)
        R = self.Rotation(angle, axis)
        W = R * V * R.Conjugate()
        return Vector(W.x, W.y, W.z)#.Normalized()

    def Rotation(self, angle, v):
        from math import sin, cos
        x = v.x * sin(float(angle)/2.0)
        y = v.y * sin(float(angle)/2.0)
        z = v.z * sin(float(angle)/2.0)
        w = cos(float(angle)/2.0)
        return Quaternion(x,y,z,w)


    def RotateByXY(self, xmoved, ymoved):
        """
        if xmoved or ymoved:
            factor = 1000.0

            yMax = ((math.pi/2)-0.1)
            yMin = 0.1
            xmoved /= factor
            ymoved /= factor
    
            self.rotX += xmoved
            self.rotY += ymoved
            self.rotX = self.rotX % (2*math.pi)
            if self.rotY > yMax:
                self.rotY = yMax
            elif self.rotY < yMin:
                self.rotY = yMin

            view = self.view#Vector(0.0, 0.0, 1.0)
            pos = Vector(self.posx, self.posy, self.posz)
            axis = (view-pos).Cross(Vector(0.0,1.0,0.0)).Normalized()
            #view = self.RotateVert(view, -self.rotY, axis)
            #self.view = self.RotateVert(view, -self.rotX, Vector(0, 1.0, 0))
            view = self.RotateVert(view, -ymoved, axis)
            self.view = self.RotateVert(view, -xmoved, Vector(0, 1.0, 0))
        """
        self.pitchDegrees += float(ymoved)/10.0
        if self.pitchDegrees >= 89.9:
            self.pitchDegrees = 89.9
        if self.pitchDegrees <= -89.9:
            self.pitchDegrees = -89.9
        self.headingDegrees += float(xmoved)/10.0

    def ApplyCamera(self):
	self.qPitch.CreateFromAxisAngle(1.0, 0.0, 0.0, self.pitchDegrees)
	self.qHeading.CreateFromAxisAngle(0.0, 1.0, 0.0, self.headingDegrees)

	# Combine the pitch and heading rotations and store the results in q
	q = self.qPitch * self.qHeading
	matrix = q.CreateMatrix()

	# Let OpenGL set our new prespective on the world!
	glMultMatrixf(matrix)

	# Create a matrix from the pitch Quaternion and get the j vector
	# for our direction.
	matrix = self.qPitch.CreateMatrix()
	self.directionVector.y = matrix[9]

	# Combine the heading and pitch rotations and make a matrix to get
	# the i and j vectors for our direction.
	q = self.qHeading * self.qPitch
	matrix = q.CreateMatrix()
	self.directionVector.x = matrix[8]
	self.directionVector.z = matrix[10]

	# Scale the direction by our speed.
	self.directionVector.MultScalar(self.forwardVelocity)

	# Increment our position by the vector
	#self.pos.x += self.directionVector.x
	#self.pos.y += self.directionVector.y
	#self.pos.z += self.directionVector.z

	# Translate to our new position.
	glTranslatef(-self.pos.x, -(self.pos.y), self.pos.z) # 아 이게 왜 방향이 다 엉망인 이유였구만.... -z를 써야되는데-_-

        #glTranslatef(self.posx, self.posy, self.posz)
        #pos = Vector(self.posx, self.posy, self.posz).Normalized()
        #glpLookAt(pos, self.view,
        #        Vector(0.0, 1.0, 0.0).Normalized())

    def GetDirV(self):
	matrix = self.qPitch.CreateMatrix()
        dirV = Vector()
	dirV.y = matrix[9]
	q = self.qHeading * self.qPitch
	matrix = q.CreateMatrix()
	dirV.x = matrix[8]
	dirV.z = matrix[10]
	dirV.w = 1.0
        return dirV.Normalized()

    def Move(self, x, y, z, theT):
        # 이걸..... 음..... 현재 가리키는 방향 즉 현재 보는 방향을 알아내서
        # 그걸 기준으로 앞뒤좌우로 움직여야 한다.
        # 앞뒤벡터를 회전벡터로 회전시킨 후에 포지션에다 더하고 빼면 됨.
        #
        #
        # 자. 이제 여기서는 y값을 절대로 변경시키지 못한다!

        lrV = Vector(x/10.0, 0.0, 0.0, 1.0)
        fbV = Vector(0.0, 0.0, z/10.0, 1.0)
	self.qPitch.CreateFromAxisAngle(1.0, 0.0, 0.0, self.pitchDegrees)
	self.qHeading.CreateFromAxisAngle(0.0, 1.0, 0.0, self.headingDegrees)

	# Combine the pitch and heading rotations and store the results in q
	q = self.qPitch * self.qHeading
	matrix = q.CreateMatrix()
        lrV = lrV.MultMatrix(matrix)
        fbV = fbV.MultMatrix(matrix)


	# Combine the heading and pitch rotations and make a matrix to get
	# the i and j vectors for our direction.
        self.directionVector = self.GetDirV()
        factor = float(theT)*20/1000.0
        if factor < 0.0:
            factor = 0.0
        if factor*AppSt.speed > 1.0:
            factor = 1.0/AppSt.speed
        self.directionVector = self.directionVector.Normalized()
        if z and not x:
            factor *= 0.5
            upVector = Vector(0.0, 1.0, 0.0)
            leftVec = upVector.Cross(self.directionVector)
            leftVec = leftVec.MultScalar(-z).Normalized()
            forVector = upVector.Cross(leftVec)
            while factor > 1.0:
                forVector = upVector.Cross(leftVec).Normalized()
                forVector = forVector.MultScalar(AppSt.speed)
                forVector = self.directionVector.Normalized().MultScalar(z).MultScalar(AppSt.speed)+forVector
                self.pos += forVector
                factor -= 1.0
            forVector = upVector.Cross(leftVec).Normalized()
            forVector = forVector.MultScalar(AppSt.speed*factor)
            forVector = self.directionVector.Normalized().MultScalar(z).MultScalar(AppSt.speed*factor)+forVector
            self.pos += forVector

        if x and not z:
            upVector = Vector(0.0, 1.0, 0.0)
            leftVec = upVector.Cross(self.directionVector).MultScalar(x)
            while factor > 1.0:
                leftVec = leftVec.Normalized().MultScalar(AppSt.speed)
                self.pos += leftVec
                factor -= 1.0
            leftVec = leftVec.Normalized().MultScalar(AppSt.speed*factor)
            self.pos += leftVec


        """
        self.posx += x
        self.posy += y
        self.posz += z
        if self.posz > -0.15:
            self.posz = -0.15
        if self.posz < -10.0:
            self.posz = -10.0
        """


def normalize(x, y, z):
    factor = 1.0/math.sqrt(x**2+y**2+z**2)
    return x*factor, y*factor, z*factor
def cross(x,y,z,x2,y2,z2):
    return ((y*z2-z*y2),(z*x2-x*z2),(x*y2-y*x2))
def dot(x,y,z,x2,y2,z2):
    return x*x2+y*y2+z*z2

class FPS:
    def __init__(self):
        self.fpsCounter = 0
        self.fpsSum = 0
        self.start = 0.0
        self.end = 0.0
        self.delay = 4000
        self.sumStart = pygame.time.get_ticks()
    def Start(self):
        timetaken = float(self.end-self.start)
        if timetaken == 0: timetaken = 1.0
        fps = 1000.0/timetaken
        self.fpsSum += fps
        self.fpsCounter += 1
        self.start = pygame.time.get_ticks()

    def End(self):
        self.end = pygame.time.get_ticks()
    def GetFPS(self):
        if self.fpsCounter == 0:
            fps = 0
        else:
            fps = self.fpsSum/self.fpsCounter
        tick = pygame.time.get_ticks()
        if tick - self.sumStart > self.delay:
            self.sumStart = pygame.time.get_ticks()
            self.fpsCounter = 0
            self.fpsSum = 0
        return fps


def InRect(x,y,w,h, x2, y2):
    if x <= x2 < x+w and y <= y2 < y+h:
        return True
    else:
        return False

g_id = 0

BLOCK_EMPTY = GenId()
BLOCK_WATER = GenId()
BLOCK_GLASS = GenId()
BLOCK_LAVA = GenId()
BLOCK_COBBLESTONE = GenId()
BLOCK_LOG = GenId()
BLOCK_WALL = GenId()
BLOCK_BRICK = GenId()
BLOCK_TNT = GenId()
BLOCK_STONE = GenId()

BLOCK_SAND = GenId()
BLOCK_GRAVEL = GenId()
BLOCK_WOOD = GenId()
BLOCK_LEAVES = GenId()
BLOCK_SILVER = GenId()
BLOCK_GOLD = GenId()
BLOCK_COALORE = GenId()
BLOCK_IRONORE = GenId()
BLOCK_DIAMONDORE = GenId()
BLOCK_IRON = GenId()

BLOCK_DIAMOND = GenId()
BLOCK_CPU = GenId()
BLOCK_CODE = GenId()
BLOCK_ENERGY = GenId()
BLOCK_KEYBIND = GenId()
BLOCK_PANELSWITCH = GenId()
BLOCK_LEVER = GenId()
BLOCK_WALLSWITCH = GenId()
BLOCK_NUMPAD = GenId()
BLOCK_TELEPORT = GenId()

BLOCK_JUMPER = GenId()
BLOCK_ELEVATOR = GenId()
BLOCK_ENGINECORE = GenId()
BLOCK_CONSTRUCTIONSITE = GenId()
BLOCK_AREASELECTOR = GenId()
BLOCK_GOLDORE = GenId()
BLOCK_SILVERORE = GenId()
BLOCK_WOOL = GenId()
BLOCK_GRASS = GenId()
BLOCK_DIRT = GenId()
BLOCK_INDESTRUCTABLE = GenId()
BLOCK_CHEST = GenId()
BLOCK_SPAWNER = GenId()


class Item(object):
    def __init__(self, type_, count, stackable = False, name="Item", color=None, inv=None, entity=None, stats=[]):
        self.type_ = type_
        self.maxLen = 64
        self.stackable = stackable
        self.name = name
        self.count = count
        self.color = color
        self.optionalInventory = inv
        self.entity = entity
        self.stats = stats

class Block(Item):
    def __init__(self, type_, count):
        Item.__init__(self, type_, count, True, "Block")

class Inventory(object):
    def __init__(self):
        self.items = [None for i in range(60)]
        self.quickItems = [None for i in range(10)]

class WorldObject(object):
    def __init__(self, time_, type_, pos):
        self.t = time_
        self.type_ 
        self.pos = pos

BLOCK_TEX_COORDS = [0,0, 0,0, 0,0,
    14,0, 14,0, 14,0,
    1,3, 1,3, 1,3,
    1,5, 1,5, 1,5,
    1,0, 1,0, 1,0,
    5,1, 4,1, 5,1,
    3,5, 3,5, 3,5,
    7,0, 7,0, 7,0,
    9,0, 8,0, 10,0,
    0,1, 0,1, 0,1,

    2,1, 2,1, 2,1,
    3,1, 3,1, 3,1,
    4,0, 4,0, 4,0,
    6,1, 6,1, 6,1,
    7,1, 7,2, 7,3,
    8,1, 8,2, 8,3,
    2,2, 2,2, 2,2,
    0,2, 0,2, 0,2,
    1,6, 1,6, 1,6,
    0,0, 0,0, 0,0,

    0,0, 0,0, 0,0,
    9,4, 9,4, 9,4,
    7,4, 7,4, 7,4,
    10,4, 10,4, 10,4,
    11,4, 11,4, 11,4,
    0,0, 0,0, 0,0,
    0,0, 0,0, 0,0,
    0,0, 0,0, 0,0,
    0,0, 0,0, 0,0,
    0,0, 0,0, 0,0,
    0,0, 0,0, 0,0,

    0,0, 0,0, 0,0,
    0,0, 0,0, 0,0,
    0,0, 0,0, 0,0,
    0,0, 0,0, 0,0,
    12,6, 12,6, 12,6,
    13,6, 13,6, 13,6,
    0,0, 0,0, 0,0,
    0,0, 3,0, 2,0,
    2,0, 2,0, 2,0,
    2,7,2,7,2,7,
    11,0,11,0,11,0,
    8,4, 8,4, 8,4,
    
    ]


def DrawCubeArm(pos,bound, color, tex1,tex2,tex3,tex4,tex5,tex6, texid, flipX = False, offset=64.0): # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
    x,y,z = pos
    w,h,j = bound
    x -= w/2
    y -= 0#h/2
    z -= j/2

    vidx = [ 
            (4, 5, 1, 0),  # bottom    
            (6,7,3, 2),  # top
            (3, 7, 4, 0),  # left
            (6,2,1, 5),  # right
            (7,6,5, 4),  # back
            (2,3,0, 1),  # front
            ]

    v = [   (0.0+x, 0.0+y-h, j+z),
            (w+x, 0.0+y-h, j+z),
            (w+x, y, j+z),
            (0.0+x, y, j+z),
            (0.0+x, 0.0+y-h, 0.0+z),
            (w+x, 0.0+y-h, 0.0+z),
            (w+x, y, 0.0+z),
            (0.0+x, y, 0.0+z) ]

    offset = offset/512.0
    for face in range(6):
        if face == 0:
            texc = [
                    (tex1[0]+offset, tex1[1]),
                    (tex1[0], tex1[1]),
                    (tex1[0], tex1[1]+offset),
                    (tex1[0]+offset, tex1[1]+offset),
                    ]
        elif face == 1:
            texc = [
                    (tex2[0]+offset, tex2[1]),
                    (tex2[0], tex2[1]),
                    (tex2[0], tex2[1]+offset),
                    (tex2[0]+offset, tex2[1]+offset),
                    ]

        elif face == 2:
            texc = [
                    (tex3[0]+offset, tex3[1]),
                    (tex3[0], tex3[1]),
                    (tex3[0], tex3[1]+offset),
                    (tex3[0]+offset, tex3[1]+offset),
                    ]

        elif face == 3:
            texc = [
                    (tex4[0]+offset, tex4[1]),
                    (tex4[0], tex4[1]),
                    (tex4[0], tex4[1]+offset),
                    (tex4[0]+offset, tex4[1]+offset),
                    ]

        elif face == 4:
            if flipX:
                texc = [
                        (tex5[0], tex5[1]),
                        (tex5[0]+offset, tex5[1]),
                        (tex5[0]+offset, tex5[1]+offset),
                        (tex5[0], tex5[1]+offset),
                        ]

            else:
                texc = [
                        (tex5[0]+offset, tex5[1]),
                        (tex5[0], tex5[1]),
                        (tex5[0], tex5[1]+offset),
                        (tex5[0]+offset, tex5[1]+offset),
                        ]

        elif face == 5:
            if flipX:
                texc = [
                        (tex6[0], tex6[1]),
                        (tex6[0]+offset, tex6[1]),
                        (tex6[0]+offset, tex6[1]+offset),
                        (tex6[0], tex6[1]+offset),
                        ]

            else:
                texc = [
                        (tex6[0]+offset, tex6[1]),
                        (tex6[0], tex6[1]),
                        (tex6[0], tex6[1]+offset),
                        (tex6[0]+offset, tex6[1]+offset),
                        ]

        v1, v2, v3, v4 = vidx[face]
        glBegin(GL_QUADS)
        glColor4ub(*color)
        glTexCoord2f(*texc[0])
        glVertex( v[v1] )
        glTexCoord2f(*texc[1])
        glVertex( v[v2] )
        glTexCoord2f(*texc[2])
        glVertex( v[v3] )
        glTexCoord2f(*texc[3])
        glVertex( v[v4] )            
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor4f(0.0, 0.0, 0.0, 1.0)
        glVertex( v[v1] )
        glVertex( v[v2] )
        glVertex( v[v2] )
        glVertex( v[v3] )
        glVertex( v[v3] )
        glVertex( v[v4] )            
        glVertex( v[v4] )            
        glVertex( v[v1] )
        glEnd()
        glEnable(GL_TEXTURE_2D)
def DrawCubeStair(pos,bound, color, tex1,tex2,tex3,tex4,tex5,tex6, texid, flipX = False, offset=32.0): # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
    x,y,z = pos
    w,h,j = bound
    vidx = [ 
            (4, 5, 1, 0),  # bottom    
            (6,7,3, 2),  # top
            (3, 7, 4, 0),  # left
            (6,2,1, 5),  # right
            (7,6,5, 4),  # back
            (2,3,0, 1),  # front
            ]

    v = [   (0.0+x, 0.0+y, j+z),
            (w+x, 0.0+y, j+z),
            (w+x, h+y, j+z),
            (0.0+x, h+y, j+z),
            (0.0+x, 0.0+y, 0.0+z),
            (w+x, 0.0+y, 0.0+z),
            (w+x, h+y, 0.0+z),
            (0.0+x, h+y, 0.0+z) ]

    offset = offset/512.0
    for face in range(6):
        if face == 0:
            texc = [
                    (tex1[0]+offset, tex1[1]),
                    (tex1[0], tex1[1]),
                    (tex1[0], tex1[1]+offset),
                    (tex1[0]+offset, tex1[1]+offset),
                    ]
        elif face == 1:
            texc = [
                    (tex2[0]+offset, tex2[1]),
                    (tex2[0], tex2[1]),
                    (tex2[0], tex2[1]+offset),
                    (tex2[0]+offset, tex2[1]+offset),
                    ]

        elif face == 2:
            texc = [
                    (tex3[0]+offset, tex3[1]),
                    (tex3[0], tex3[1]),
                    (tex3[0], tex3[1]+offset),
                    (tex3[0]+offset, tex3[1]+offset),
                    ]

        elif face == 3:
            texc = [
                    (tex4[0]+offset, tex4[1]),
                    (tex4[0], tex4[1]),
                    (tex4[0], tex4[1]+offset),
                    (tex4[0]+offset, tex4[1]+offset),
                    ]

        elif face == 4:
            if flipX:
                texc = [
                        (tex5[0], tex5[1]),
                        (tex5[0]+offset, tex5[1]),
                        (tex5[0]+offset, tex5[1]+offset),
                        (tex5[0], tex5[1]+offset),
                        ]

            else:
                texc = [
                        (tex5[0]+offset, tex5[1]),
                        (tex5[0], tex5[1]),
                        (tex5[0], tex5[1]+offset),
                        (tex5[0]+offset, tex5[1]+offset),
                        ]

        elif face == 5:
            if flipX:
                texc = [
                        (tex6[0], tex6[1]),
                        (tex6[0]+offset, tex6[1]),
                        (tex6[0]+offset, tex6[1]+offset),
                        (tex6[0], tex6[1]+offset),
                        ]

            else:
                texc = [
                        (tex6[0]+offset, tex6[1]),
                        (tex6[0], tex6[1]),
                        (tex6[0], tex6[1]+offset),
                        (tex6[0]+offset, tex6[1]+offset),
                        ]

        v1, v2, v3, v4 = vidx[face]
        glBegin(GL_QUADS)
        glColor4ub(*color)
        glTexCoord2f(*texc[0])
        glVertex( v[v1] )
        glTexCoord2f(*texc[1])
        glVertex( v[v2] )
        glTexCoord2f(*texc[2])
        glVertex( v[v3] )
        glTexCoord2f(*texc[3])
        glVertex( v[v4] )            
        glEnd()
def DrawCube(pos,bound, color, tex1,tex2,tex3,tex4,tex5,tex6, texid, flipX = False, offset=64.0): # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
    x,y,z = pos
    w,h,j = bound
    x -= w/2
    y -= h/2
    z -= j/2

    vidx = [ 
            (4, 5, 1, 0),  # bottom    
            (6,7,3, 2),  # top
            (3, 7, 4, 0),  # left
            (6,2,1, 5),  # right
            (7,6,5, 4),  # back
            (2,3,0, 1),  # front
            ]

    v = [   (0.0+x, 0.0+y, j+z),
            (w+x, 0.0+y, j+z),
            (w+x, h+y, j+z),
            (0.0+x, h+y, j+z),
            (0.0+x, 0.0+y, 0.0+z),
            (w+x, 0.0+y, 0.0+z),
            (w+x, h+y, 0.0+z),
            (0.0+x, h+y, 0.0+z) ]

    offset = offset/512.0
    for face in range(6):
        if face == 0:
            texc = [
                    (tex1[0]+offset, tex1[1]),
                    (tex1[0], tex1[1]),
                    (tex1[0], tex1[1]+offset),
                    (tex1[0]+offset, tex1[1]+offset),
                    ]
        elif face == 1:
            texc = [
                    (tex2[0]+offset, tex2[1]),
                    (tex2[0], tex2[1]),
                    (tex2[0], tex2[1]+offset),
                    (tex2[0]+offset, tex2[1]+offset),
                    ]

        elif face == 2:
            texc = [
                    (tex3[0]+offset, tex3[1]),
                    (tex3[0], tex3[1]),
                    (tex3[0], tex3[1]+offset),
                    (tex3[0]+offset, tex3[1]+offset),
                    ]

        elif face == 3:
            texc = [
                    (tex4[0]+offset, tex4[1]),
                    (tex4[0], tex4[1]),
                    (tex4[0], tex4[1]+offset),
                    (tex4[0]+offset, tex4[1]+offset),
                    ]

        elif face == 4:
            if flipX:
                texc = [
                        (tex5[0], tex5[1]),
                        (tex5[0]+offset, tex5[1]),
                        (tex5[0]+offset, tex5[1]+offset),
                        (tex5[0], tex5[1]+offset),
                        ]

            else:
                texc = [
                        (tex5[0]+offset, tex5[1]),
                        (tex5[0], tex5[1]),
                        (tex5[0], tex5[1]+offset),
                        (tex5[0]+offset, tex5[1]+offset),
                        ]

        elif face == 5:
            if flipX:
                texc = [
                        (tex6[0], tex6[1]),
                        (tex6[0]+offset, tex6[1]),
                        (tex6[0]+offset, tex6[1]+offset),
                        (tex6[0], tex6[1]+offset),
                        ]

            else:
                texc = [
                        (tex6[0]+offset, tex6[1]),
                        (tex6[0], tex6[1]),
                        (tex6[0], tex6[1]+offset),
                        (tex6[0]+offset, tex6[1]+offset),
                        ]

        v1, v2, v3, v4 = vidx[face]
        glBegin(GL_QUADS)
        glColor4ub(*color)
        glTexCoord2f(*texc[0])
        glVertex( v[v1] )
        glTexCoord2f(*texc[1])
        glVertex( v[v2] )
        glTexCoord2f(*texc[2])
        glVertex( v[v3] )
        glTexCoord2f(*texc[3])
        glVertex( v[v4] )            
        glEnd()
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor4f(0.0, 0.0, 0.0, 1.0)
        glVertex( v[v1] )
        glVertex( v[v2] )
        glVertex( v[v2] )
        glVertex( v[v3] )
        glVertex( v[v3] )
        glVertex( v[v4] )            
        glVertex( v[v4] )            
        glVertex( v[v1] )
        glEnd()

g_ID = 0
ANIM_IDLE = GenId()
ANIM_WALK = GenId()
ANIM_ATTACK = GenId()
ANIM_HIT = GenId()

g_ID = 0
MOB_SKELETON = GenId()


class MobGL(object):
    def __init__(self, pos, bound, skin, type_, color, entity):
        self.pos = pos
        self.bound = bound
        self.skin = skin


        self.type_ = type_
        self.color = color
        self.entity = entity

        self.animstate = ANIM_WALK
        self.animMax = 60.0
        self.animIdx = -self.animMax
        self.t = 0
        self.fps = 15.0/6.0
        self.flip = False

        self.dList = None
        self.genDone = False


        self.prevY = 0.0
        self.jumpStartT = 0
        self.jumping = False
        self.canJump = False
        self.jumpTime = 350
        self.jumpHeight = 1.9
        self.prevFactor = 0.0
        self.prevFall = -1

        self.prevJump = 0
        self.jumpDelay = 700
        self.prevJumpY = 0.0
        self.speed = 0.1
        self.angle = 0.0
        # 방향이동, 점프등을 구현한다.
        # 이동하는 방향으로 dir벡터를 구하고
        # dir벡터의 각도를 구해서 회전을 한다.
        # 점프를 하면서 막 플레이어의 위치로 이동하면 됨
        self.attackDelay = 3000
        self.prevAtk = 0
        self.prevWalk = 0
        self.entity.BindHit(self.OnHit)
        self.entity.BindDead(self.OnDead)
        self.prevHit = 0
        self.hitRecovery = 250



    def OnDead(self, attacker):
        AppSt.mobs.remove(self)
        print 'dead'
    def OnHit(self, attacker):
        self.animstate = ANIM_HIT
        self.prevHit = pygame.time.get_ticks()
    def Tick(self,t,m,k):
        def AIAttacker():
            if self.PlayerInSpot():
                if self.Range() > 1.2:
                    if t-self.prevJump > self.jumpDelay:
                        self.prevJump = t
                        if self.canJump and not self.jumping:
                            self.StartJump(t)
                    self.WalkToPlayer(t-self.prevWalk)
                    self.UpdateDirection()
                else:
                    if t - self.prevAtk > self.attackDelay:
                        self.prevAtk = t
                        self.UpdateDirection()
                        self.AttackPlayer()
                    elif t - self.prevAtk > self.attackDelay/6:
                        self.animIdx = -self.animMax
                        self.flip = False
                        self.animstate = ANIM_IDLE
            else:
                self.animIdx = -self.animMax
                self.flip = False
                self.animstate = ANIM_IDLE
        if t - self.prevHit > self.hitRecovery:
            AIAttacker()
            self.prevWalk = t
        self.FallOrJump(t)

    def AttackPlayer(self):
        self.entity.Attack(AppSt.entity)
        AppSt.sounds["Hit2"].play()
        self.animIdx = -self.animMax
        self.flip = False
        self.animstate = ANIM_ATTACK
    def Range(self):
        pos = AppSt.cam1.pos
        pos = Vector(pos.x,0,-pos.z)
        mypos = Vector(self.pos[0], 0, self.pos[2])
        return (mypos-pos).Length()
    def PlayerInSpot(self):
        pos = AppSt.cam1.pos
        pos = Vector(pos.x,pos.y,-pos.z)
        mypos = Vector(*self.pos)
        if (mypos-pos).Length() < 10.0:
            return True
        else:
            return False

    def UpdateDirection(self):
        pos = AppSt.cam1.pos
        pos = Vector(pos.x,pos.y,-pos.z)
        mypos = Vector(*self.pos)
        dirV = pos-mypos
        dirV.y = 0
        dirV = dirV.Normalized()
        self.angle = Vector2ToAngle(dirV.x, dirV.z)
    def WalkToPlayer(self, theT):
        self.animstate = ANIM_WALK
        pos = AppSt.cam1.pos
        pos = Vector(pos.x,pos.y,-pos.z)
        mypos = Vector(*self.pos)
        dirV = pos-mypos
        dirV.y = 0
        factor = float(theT)*20.0/1000.0

        if factor < 0.0:
            factor = 0.0
        while factor >= 1.0:
            dirV = dirV.Normalized().MultScalar(self.speed)
            self.pos = x,y,z = AppSt.chunks.FixPos(mypos, mypos+dirV, self.bound)
            factor -= 1.0
        dirV = dirV.Normalized().MultScalar(self.speed*factor)
        self.pos = x,y,z = AppSt.chunks.FixPos(mypos, mypos+dirV, self.bound)


    def CheckJump(self, y):
        if self.prevY - 0.15 <= y <= self.prevY + 0.15:
            self.canJump = True
        else:
            self.canJump = False
        self.prevY = y

    def StartJump(self, t):
        self.jumpStartT = t
        self.jumping = True
        self.canJump = False
    def DoJump(self, t):
        if t-self.jumpStartT < self.jumpTime:
            x,y,z = self.pos
            factor = (float(t)-float(self.jumpStartT))/float(self.jumpTime)
            jump = (factor-self.prevFactor)*self.jumpHeight
            self.prevFactor = factor
            
            x,y,z = AppSt.chunks.FixPos(Vector(x,y,z), Vector(x,y+jump,z), self.bound)
            self.pos = x,y,z
            if y == self.prevJumpY:
                self.prevFactor = 0.0
                self.jumping = False
            self.prevJumpY = y
        else:
            self.prevFactor = 0.0
            self.jumping = False

    def FallOrJump(self, t):
        if self.jumping:
            self.DoJump(t)
            self.prevFall = t
        else:
            x,y,z = self.pos
            if not AppSt.chunks.InWater(x,y,z) and not AppSt.chunks.InWater(x,y-1.0,z):
                factor = (t-self.prevFall)*35.0/1000.0
                if factor < 0.0:
                    factor = 0.0
                while factor >= 1.0:
                    x,y,z = AppSt.chunks.FixPos(Vector(x,y,z), Vector(x,y-(self.speed),z), self.bound)
                    factor -= 1.0
                x,y,z = AppSt.chunks.FixPos(Vector(x,y,z), Vector(x,y-(self.speed*factor),z), self.bound)
                self.pos = x,y,z
                self.CheckJump(y)
            self.prevFall = t

    def SetAnimState(self, s):
        self.animstate = s
    def Render2(self, nameRenderer, cam, t):
        if not self.genDone or AppSt.regenTex:
            self.dList = [glGenLists(1) for i in range(6)]
        glBindTexture(GL_TEXTURE_2D, AppSt.mobtex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)



        x,y,z = self.pos
        y -= self.bound[1]
        w,h,l = self.bound

        factor = self.animIdx/self.animMax
        glPushMatrix()
        glTranslatef(x,y,z)
        glRotatef(-self.angle+90, 0.0, 1.0, 0.0)

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[0]
        glPushMatrix()
        h = 1.5
        top = h-(0.25)+0.5
        glTranslatef(0,top,0)
        if self.animstate == ANIM_HIT:
            glRotatef(-30, 1.0, 0.0, 0.0)
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[0], GL_COMPILE)
            DrawCube((0,0,0), (0.25, 0.25, 0.15), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[0])
        glPopMatrix()

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[1]
        glPushMatrix()
        mid = h-(0.25)+0.25/2-(0.5)+0.5
        glTranslatef(0,0+mid,0)
        glRotatef(0, 0.0, 1.0, 0.0)
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[1], GL_COMPILE)
            DrawCube((0,0,0),(0.4, 0.5, 0.25), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[1])

        glPopMatrix()

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[2]
        glPushMatrix()
        glTranslatef(0-0.25,0+mid+0.25,0)
        if self.animstate == ANIM_WALK:
            glRotatef(factor*45, 1.0, 0.0, 0.0)
        elif self.animstate == ANIM_IDLE:
            pass
        elif self.animstate == ANIM_ATTACK:
            glRotatef(-90, 1.0, 0.0, 0.0)
            glRotatef(factor*45, 1.0, 0.0, 0.0)
            glRotatef(factor*45, 0.0, 0.0, 1.0)
        elif self.animstate == ANIM_HIT:
            glRotatef(-30, 1.0, 0.0, 0.0)

        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[2], GL_COMPILE)
            DrawCubeArm((0,0,0),(0.1, 0.5, 0.1), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[2])
        glPopMatrix() # 오른팔

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[3]
        glPushMatrix()
        glTranslatef(0+0.25,0+mid+0.25,0)
        if self.animstate == ANIM_WALK:
            glRotatef(-factor*45, 1.0, 0.0, 0.0)
        elif self.animstate == ANIM_IDLE:
            pass
        elif self.animstate == ANIM_HIT:
            glRotatef(-30, 1.0, 0.0, 0.0)
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[3], GL_COMPILE)
            DrawCubeArm((0,0,0),(0.1, 0.5, 0.1), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[3])
        glPopMatrix() # 왼팔

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[4]
        glPushMatrix()
        glTranslatef(0-0.075,0+mid-0.5+0.25,0)
        if self.animstate == ANIM_WALK:
            glRotatef(-factor*45, 1.0, 0.0, 0.0)
        elif self.animstate == ANIM_IDLE:
            pass
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[4], GL_COMPILE)
            DrawCubeArm((0,0,0),(0.15, 0.5, 0.15), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[4])
        glPopMatrix() # 오른발

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[5]
        glPushMatrix()
        glTranslatef(0+0.075,0+mid-0.5+0.25,0)
        if self.animstate == ANIM_WALK:
            glRotatef(factor*45, 1.0, 0.0, 0.0)
        elif self.animstate == ANIM_IDLE:
            pass
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[5], GL_COMPILE)
            DrawCubeArm((0,0,0),(0.15, 0.5, 0.15), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex, True) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[5])
        glPopMatrix() # 왼발


        self.genDone = True
        if self.t and self.flip:
            self.animIdx -= (t-self.t)/float(self.fps)
        elif self.t:
            self.animIdx += (t-self.t)/float(self.fps)
        if self.animIdx > self.animMax:
            self.animIdx = self.animMax
            self.flip = True
        elif self.animIdx < -self.animMax:
            self.animIdx = -self.animMax
            self.flip = False
        self.t = t

        glPopMatrix()
    def Render(self, nameRenderer, cam, t):
        if not self.genDone or AppSt.regenTex:
            self.dList = [glGenLists(1) for i in range(6)]
        glBindTexture(GL_TEXTURE_2D, AppSt.mobtex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)



        x,y,z = self.pos
        y -= self.bound[1]
        w,h,l = self.bound

        factor = self.animIdx/self.animMax
        glPushMatrix()
        glTranslatef(x,y,z)
        glRotatef(-self.angle+90, 0.0, 1.0, 0.0)

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[0]
        glPushMatrix()
        h = 1.5
        top = h-(0.25)+0.5
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[0], GL_COMPILE)
            glTranslatef(0,top,0)
            if self.animstate == ANIM_HIT:
                glRotatef(-30, 1.0, 0.0, 0.0)
            DrawCube((0,0,0), (0.25, 0.25, 0.15), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[0])
        glPopMatrix()

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[1]
        glPushMatrix()
        mid = h-(0.25)+0.25/2-(0.5)+0.5
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[1], GL_COMPILE)
            glTranslatef(0,0+mid,0)
            glRotatef(0, 0.0, 1.0, 0.0)
            DrawCube((0,0,0),(0.4, 0.5, 0.25), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[1])

        glPopMatrix()

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[2]
        glPushMatrix()
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[2], GL_COMPILE)
            glTranslatef(0-0.25,0+mid+0.25,0)
            if self.animstate == ANIM_WALK:
                glRotatef(factor*45, 1.0, 0.0, 0.0)
            elif self.animstate == ANIM_IDLE:
                pass
            elif self.animstate == ANIM_ATTACK:
                glRotatef(-90, 1.0, 0.0, 0.0)
                glRotatef(factor*45, 1.0, 0.0, 0.0)
                glRotatef(factor*45, 0.0, 0.0, 1.0)
            elif self.animstate == ANIM_HIT:
                glRotatef(-30, 1.0, 0.0, 0.0)

            DrawCubeArm((0,0,0),(0.1, 0.5, 0.1), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[2])
        glPopMatrix() # 오른팔

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[3]
        glPushMatrix()
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[3], GL_COMPILE)
            glTranslatef(0+0.25,0+mid+0.25,0)
            if self.animstate == ANIM_WALK:
                glRotatef(-factor*45, 1.0, 0.0, 0.0)
            elif self.animstate == ANIM_IDLE:
                pass
            elif self.animstate == ANIM_HIT:
                glRotatef(-30, 1.0, 0.0, 0.0)
            DrawCubeArm((0,0,0),(0.1, 0.5, 0.1), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[3])
        glPopMatrix() # 왼팔

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[4]
        glPushMatrix()
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[4], GL_COMPILE)
            glTranslatef(0-0.075,0+mid-0.5+0.25,0)
            if self.animstate == ANIM_WALK:
                glRotatef(-factor*45, 1.0, 0.0, 0.0)
            elif self.animstate == ANIM_IDLE:
                pass
            DrawCubeArm((0,0,0),(0.15, 0.5, 0.15), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[4])
        glPopMatrix() # 오른발

        tex1,tex2,tex3,tex4,tex5,tex6 = self.skin[5]
        glPushMatrix()
        if not self.genDone or AppSt.regenTex:
            glNewList(self.dList[5], GL_COMPILE)
            glTranslatef(0+0.075,0+mid-0.5+0.25,0)
            if self.animstate == ANIM_WALK:
                glRotatef(factor*45, 1.0, 0.0, 0.0)
            elif self.animstate == ANIM_IDLE:
                pass
            DrawCubeArm((0,0,0),(0.15, 0.5, 0.15), self.color, tex1,tex2,tex3,tex4,tex5,tex6, AppSt.mobtex, True) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
            glEndList()
        else:
            glCallList(self.dList[5])
        glPopMatrix() # 왼발


        self.genDone = True
        if self.t and self.flip:
            self.animIdx -= (t-self.t)/float(self.fps)
        elif self.t:
            self.animIdx += (t-self.t)/float(self.fps)
        if self.animIdx > self.animMax:
            self.animIdx = self.animMax
            self.flip = True
        elif self.animIdx < -self.animMax:
            self.animIdx = -self.animMax
            self.flip = False
        self.t = t

        glPopMatrix()

class FightingElements(object):
    def __init__(self, id_, name, pos, params):
        self.id = id_
        self.name = name
        self.pos = pos
        self.params = params

    def OnAttack(self, attacker, defenders):
        # 이렇게 하지 말고 일단 전투를 구현한 다음에 하나하나 유틸라이즈하자.
        pass

class FightingEntity(object):
    def __init__(self, id_, name, pos, params):
        # 복잡하게 str이 체력을 올려주고 이러지 말고
        # str은 밀리무기 공격력
        # dex는 레인지 무기 공격력
        # int는 마법파워 이렇게 올리고
        # 여러가지를 둔다.
        # 연사력은 그냥 다 똑같음?
        # 멀티는 하지 말고 싱글만 만들자.
        self.id = id_
        self.name = name
        self.pos = pos
        self.basehp = params["hp"]
        self.basemp = params["mp"]
        self.str = params["str"]
        self.dex = params["dex"]
        self.int = params["int"]
        self.curhp = self.basehp
        self.curmp = self.basemp
        self.eqs = [] # 몹일경우 여기에 담고
        self.inventory = [] # 플레이어일경우 그냥 링크일 뿐
        # 순수하게 element만 담으면 뭔가 퍼즐이 맞을 거 같지만 아이템 자체를 담아야함.
        # 아이템의 속성에 texture뭘쓸건지도 나중에 넣어줘야함. 종류가 많아지면 후덜덜...XXX:
        # 하여간에 그리하여 공격 방어는 entity끼리 싸우게 된다.
        # 음...아니면 걍 텍스쳐 종류는 적은 수로 유지하고 컬러만 바꾸도록 해보자. 컬러가 달라도 다른 품질일 수도 있고말이지.
        # 블럭들은 마우스를 댔을때 설명이 필요없다.
        # 하지만 토치 상자등이나 코드블럭 스포너 아이템등은 설명이 필요하다.
        # 코드와 스포너를 잘써서 타워디펜스를 만들 수도 있을 것이고 상점을 만들 수도 있을 것이고 뭐....
        # NPC는 또다른 코드블럭이다. 단지, npc는 스포너가 없고 메뉴 인터랙션으로 출력을 하는 정도?
        def A(other):
            pass
        self.ondead = A
        self.onhit = A

    def BindDead(self, func):
        self.ondead = func
    def BindHit(self, func):
        self.onhit = func
    def Attack(self, other):
        other.curhp -= 20
        other.onhit(self)
        if other.IsDead():
            other.ondead(self)
    def IsDead(self):
        if self.curhp <= 0:
            return True
        else:
            return False


AppSt = None

from threading import Thread
import copy

class DigDigScript(object):
    def __init__(self):
        pass

    def SaveRegion(self, name_, min, max, ymin, ymax):
        assert type(min) in [str, unicode]
        assert type(max) in [str, unicode]
        spawners = {}
        for coord in AppSt.gui.spawns:
            name = AppSt.gui.spawns[coord]
            spawners[name] = coord
        min, max = spawners[min], spawners[max]
        min = list(min)
        max = list(max)
        if min[0] > max[0]:
            max[0], min[0] = min[0], max[0]
        if min[2] > max[2]:
            max[2], min[2] = min[2], max[2]
        if ymin > ymax:
            ymax, ymin = ymin, ymax
        AppSt.chunks.SaveRegion(name_, (min[0], ymin, min[2]), (max[0], ymax, max[2]))

    def LoadRegion(self, name_, pos):
        assert type(pos) in [str, unicode]
        spawners = {}
        for coord in AppSt.gui.spawns:
            name = AppSt.gui.spawns[coord]
            spawners[name] = coord
        pos = spawners[pos]
        AppSt.chunks.LoadRegion(name_, pos)
        del AppSt.gui.spawns[pos]
        # 스포너 뿐만이 아니라, 덮어씌울때 모든 아이템이나 상자등을 다 어떻게 처리한다? 아예, 그곳에 상자나 아이템이 있으면 로드하지 못하게
        # 막아야 할 것 같다. XXX:
        # 또한 복사할 때 스포너나 아이템이 복사되지 않도록 해야한다.(상자, 스포너, 코드블락)?
        # 음......여러가지 장치를 해둔 경우 그것도 복사하고 싶겠지만 그건 걍 포기??
        # 그것도 다 복사되게 해야하는 듯. 특히 복사하는 용도의 스포너는 복사하지 않고, 그 외의 스포너는 복사를 하되
        # 만약 스포너의 이름이 중복되는 경....음.................
        #
        # 아예 어드민의 용도로만 사용하게 하도록 하자 그냥;;
        # XXX: 이제 부수지 못하도록 스포너 2개로 Lockdown거는 것을 구현하자. 락다운을 걸면 땅의 주인만 락다운을 풀 수가 있음
        # 땅의 소유지를 결정하는 것도 스포너 2개로.
    def SpawnMob(self, pos):
        assert type(pos) in [str, unicode]
        spawners = {}
        for coord in AppSt.gui.spawns:
            name = AppSt.gui.spawns[coord]
            spawners[name] = coord
        pos = spawners[pos]
        skin = [
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 0*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 0*64.0/512.0),
            (1*64.0/512.0, 0*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 1*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 1*64.0/512.0)]]

        entity = FightingEntity(AppSt.GenId(), "Mob1", AppSt.cam1.pos, {"hp": 100, "mp": 100, "str": 5, "dex": 5, "int": 5})
        AppSt.mobs += [MobGL((pos[0]+0.5, pos[1]+3.0+0.5, pos[2]+0.5), [0.8,1.7,0.8], skin, MOB_SKELETON, (200,200,200,255), entity)]
class ScriptLauncher(object):
    def __init__(self, coord):
        self.code = ''
        self.lastError = ''
        self.coord = coord
        # 일정 시간이 지나면 강제종료하는 루틴도 넣는다?
        # 서버에 랙이 있다면?
        from RestrictedPython.Guards import full_write_guard
        def getmyitem(obj, name):
            if name in AppSt.gui.spawns.itervalues():
                return obj[name]
            else:
                return None

        def getmyattr(obj, name):
            assert name in ["SpawnMob", "SaveRegion", "LoadRegion"], "Cannot access that attribute"
            return getattr(obj,name)
        self.r = dict(__builtins__ = {'digdig': DigDigScript(), 'None': None, 'True': True, 'False': False, '_getitem_':getmyitem, '_write_':full_write_guard, '_getattr_':getmyattr})


    def run(self):
        if not self.code:
            return
        self.code = self.code.replace("while", "while not supported")
        self.code = self.code.replace("for", "for not supported")
        self.code = self.code.replace("def", "def not supported")
        self.code = self.code.replace("class", "class not supported")
        self.code = self.code.replace("print", "print not supported")
        self.code = self.code.replace("exec", "exec not supported")
        self.code = self.code.replace("lambda", "lambda not supported")
        self.code = self.code.replace("import", "import not supported")
        self.code = self.code.replace("del", "del not supported")
        # XXX: while이나 for같은 루프는 함수 수준에서 간략하게 지원한다.
        spawners = {}
        for coord in AppSt.gui.spawns:
            name = AppSt.gui.spawns[coord]
            spawners[name] = coord
        self.r["spawners"] = spawners

        from RestrictedPython import compile_restricted
        code = compile_restricted(self.code, 'CodeBlock (%d, %d, %d)' % self.coord, 'exec')

        try:
            exec(code) in self.r
        except:
            import traceback
            self.lastError = traceback.format_exc()
            print self.lastError

class DigDigApp(object):
    def __init__(self):
        global AppSt
        AppSt = self
        self.keyBinds = {
                "UP": K_w,
                "LEFT": K_a,
                "DOWN": K_s,
                "RIGHT": K_d,
                "ATK": K_j,
                "JUMP": K_SPACE,}
        self.delay = 50
        self.renderDelay = 1000/15
        self.prevTime = 0
        self.renderPrevTime = 0
        self.soundPrevTime = 0
        self.soundDelay = 1000/4
        self.bound = (0.5,1.7,0.5)
        self.prevY = 0.0
        self.jumpStartT = 0
        self.jumping = False
        self.canJump = False
        self.jumpTime = 350
        self.jumpHeight = 1.9
        self.prevFactor = 0.0
        self.prevFall = -1
        self.prevJumpY = 0.0
        self.speed = 0.18
        self.guiMode = False
        self.guiPrevTime = 0
        self.guiRenderDelay = 500
        self.show = True
        self.prevDig = 0
        self.digDelay = 80
        self.prevBlock = None
        self.lastBlock = None
        self.blockHP = -1
        self.blockItems = []
        self.digging = False
        
        self.attackDelay = 1000
        self.prevAttack = 0


        self.surf = pygame.Surface((512,512), flags =SRCALPHA)


    def DropItem(self, item):
        print 'DropItem'
    def DoCam(self, t, m, k):
        if not self.guiMode:
            self.cam1.RotateByXY(m.x-SW/2, m.y-SH/2)
            pygame.mouse.set_pos(SW/2, SH/2)
    def StartJump(self, t):
        self.jumpStartT = t
        self.jumping = True
        self.canJump = False
    def DoJump(self, t):
        if t-self.jumpStartT < self.jumpTime:
            x = self.cam1.pos.x
            y = self.cam1.pos.y
            z = -self.cam1.pos.z
            factor = (float(t)-float(self.jumpStartT))/float(self.jumpTime)
            jump = (factor-self.prevFactor)*self.jumpHeight
            self.prevFactor = factor
            
            x,y,z = self.chunks.FixPos(Vector(x,y,z), Vector(x,y+jump,z), self.bound)
            self.cam1.pos = Vector(x,y,-z)
            if y == self.prevJumpY:
                self.prevFactor = 0.0
                self.jumping = False
            self.prevJumpY = y
        else:
            self.prevFactor = 0.0
            self.jumping = False

    def FallOrJump(self, t):
        if self.jumping:
            self.DoJump(t)
            self.prevFall = t
        else:
            if not self.chunks.InWater(self.cam1.pos.x, self.cam1.pos.y, -self.cam1.pos.z) and not self.chunks.InWater(self.cam1.pos.x, self.cam1.pos.y-1.0, -self.cam1.pos.z):
                x = self.cam1.pos.x
                y = self.cam1.pos.y
                z = -self.cam1.pos.z
                factor = (t-self.prevFall)*35.0/1000.0
                if factor < 0.0:
                    factor = 0.0
                while factor >= 1.0:
                    x,y,z = self.chunks.FixPos(Vector(x,y,z), Vector(x,y-(self.speed),z), self.bound)
                    factor -= 1.0
                x,y,z = self.chunks.FixPos(Vector(x,y,z), Vector(x,y-(self.speed*factor),z), self.bound)

                # 여기서 계단위에 있으면 그만큼 좌표를 올려준다.
                xx,yy,zz = int(x),int(y-1.19),int(z)
                xxx = xx-(xx%32)
                yyy = yy-(yy%32)
                zzz = zz-(zz%32)
                if (xxx,yyy,zzz) in self.stairs:
                    for stair in self.stairs[(xxx,yyy,zzz)]:
                        x1,y1,z1,f,b = stair
                        if x1 <= x <= x1+1.0 and z1 <= z <= z1+1.0 and y1+1.19 <= y <= y1+2.20:
                            plus = 0
                            if f == 2:
                                plus = 1.0-(abs(x)-int(abs(x)))
                            if f == 3:
                                plus = abs(x)-int(abs(x))
                            if f == 4:
                                plus = 1.0-(abs(z)-int(abs(z)))
                            if f == 5:
                                plus = abs(z)-int(abs(z))
                            plus *= 2
                            if plus > 1.0:
                                plus = 1.0
                            x,y,z = self.chunks.FixPos(Vector(x,y,z), Vector(x,float(y1)+1.20+plus,z), self.bound)

                self.cam1.pos = Vector(x,y,-z)

                self.CheckJump(y)
            self.prevFall = t

    def RenderStairs(self, frustum):
        for xyz in self.stairs:
            stairs = self.stairs[xyz]
            if xyz not in self.stairsDL:
                self.stairsDL[xyz] = {}
            for stair in stairs:
                x,y,z,f,b = stair
                if (x,y,z) not in self.stairsDL[xyz] or self.regenTex:

                    self.stairsDL[xyz][(x,y,z)] = dList = glGenLists(1)
                    glNewList(dList, GL_COMPILE)
                    if b == ITEM_STAIR:
                        b = BLOCK_STONE
                    elif b == ITEM_WOODENSTAIR:
                        b = BLOCK_WOOD

                    texupx = (BLOCK_TEX_COORDS[b*2*3 + 0]*32.0) / 512.0
                    texupy = (BLOCK_TEX_COORDS[b*2*3 + 1]*32.0) / 512.0
                    texmidx = (BLOCK_TEX_COORDS[b*2*3 + 2]*32.0) / 512.0
                    texmidy = (BLOCK_TEX_COORDS[b*2*3 + 3]*32.0) / 512.0
                    texbotx = (BLOCK_TEX_COORDS[b*2*3 + 4]*32.0) / 512.0
                    texboty = (BLOCK_TEX_COORDS[b*2*3 + 5]*32.0) / 512.0

                    tex1 = texupx,texupy
                    tex2 = texbotx,texboty
                    tex3 = texmidx,texmidy
                    tex4 = texmidx,texmidy
                    tex5 = texmidx,texmidy
                    tex6 = texmidx,texmidy
                    if f == 2: # 왼쪽을 향한 계단
                        DrawCubeStair((x,y,z), (1.0,0.33,1.0), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                        DrawCubeStair((x+0.33,y+0.33,z), (0.66,0.33,1.0), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                        DrawCubeStair((x+0.66,y+0.66,z), (0.33,0.33,1.0), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                    elif f == 3:
                        DrawCubeStair((x,y,z), (1.0,0.33,1.0), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                        DrawCubeStair((x,y+0.33,z), (0.66,0.33,1.0), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                        DrawCubeStair((x,y+0.66,z), (0.33,0.33,1.0), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                    elif f == 4:
                        DrawCubeStair((x,y,z), (1.0,0.33,1.0), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                        DrawCubeStair((x,y+0.33,z+0.33), (1.0,0.33,0.66), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                        DrawCubeStair((x,y+0.66,z+0.66), (1.0,0.33,0.33), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                    elif f == 5:
                        DrawCubeStair((x,y,z), (1.0,0.33,1.0), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                        DrawCubeStair((x,y+0.33,z), (1.0,0.33,0.66), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                        DrawCubeStair((x,y+0.66,z), (1.0,0.33,0.33), (255,255,255,255), tex1,tex2,tex3,tex4,tex5,tex6, AppSt.tex)
                    glEndList()


                if self.chunks.CubeInFrustumPy(x+0.5,y+0.5,z+0.5,0.5,frustum):
                    glBindTexture(GL_TEXTURE_2D, self.tex)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
                    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                    glCallList(self.stairsDL[xyz][(x,y,z)])

                # 큐브 3개로 계단을 만든다. 스톤 텍스쳐를 이용하면 된다.
    def DoMove(self, t, m, k):
        if not self.guiMode:
            pressed = pygame.key.get_pressed()
            oldPos = self.cam1.pos
            x,y,z = oldPos.x,oldPos.y,oldPos.z
            if pressed[self.keyBinds["LEFT"]]:
                self.cam1.Move(-1.0,0,0, t-self.prevTime)
            if pressed[self.keyBinds["RIGHT"]]:
                self.cam1.Move(1.0,0,0, t-self.prevTime)
            if pressed[self.keyBinds["UP"]]:
                self.cam1.Move(0,0,1.0, t-self.prevTime)
            if pressed[self.keyBinds["DOWN"]]:
                self.cam1.Move(0,0,-1.0, t-self.prevTime)

            if pressed[self.keyBinds["JUMP"]]:
                if self.canJump and not self.jumping:
                    self.StartJump(t)
            #if t - self.prevTime > self.delay:
            xyz2 = self.cam1.pos#Vector(x,y,z)+((self.cam1.pos - Vector(x,y,z)).Normalized())
            x2,y2,z2 = xyz2.x, xyz2.y, xyz2.z

            x3,y3,z3 = self.chunks.FixPos(Vector(x,y,-z), Vector(x2,y2,-z2), self.bound)
            self.cam1.pos = Vector(x3,y3,-z3)

        self.prevTime = t
        self.CheckJump(self.cam1.pos.y)

    def RPressing(self,t,m,k):
        if not self.gui.invShown:
            mob = self.GetMob()
            if mob:
                self.OnMobRHit(mob, t)
                self.chColor = self.BLUE_CH
                return
    def RUp(self,t,m,k):
        self.chColor = self.WHITE_CH

    def RDown(self, t, m, k):
        # 이제 여기서 가지고있는 블럭을 쌓도록 한다.
        # 아이템 스폰할 때 오어를 스폰하고 블럭은 스폰하지 않도록도 한다. XXX:
        # 아 그런데 이제 박스같은거 클릭하면 그거 열고 그래야하네
        # 상자 동서남북은 어떻게 할까. extra block flag가 있어서 블럭이 그거면
        # 다른 버퍼에서 읽어온다는....

        # 음....아이템을 넣으면 거기에 BLOCK_ITEM을 넣어서
        # 그 블럭을 해체하면 아이템도 해체할 수 있도록 해야겠다.
        if not self.gui.invShown:
            mob = self.GetMob()
            if mob:
                self.OnMobRHit(mob, t)
                self.chColor = self.BLUE_CH
                return
        if not self.lastBlock:
            return
        x,y,z,f,b = self.lastBlock
        pos = self.cam1.pos
        pos = Vector(pos.x, pos.y, -pos.z)
        dir_ = self.cam1.GetDirV()
        dir_ = Vector(dir_.x, dir_.y, -dir_.z)
        dir_ = dir_.Normalized()
        dir_ = dir_.MultScalar(math.sqrt(2)*9.0)
        dir_ += pos

        if not self.gui.invShown:
            if (x,y,z) in self.gui.boxes:
                self.gui.selectedBox = self.gui.boxes[(x,y,z)]
                self.gui.toolMode = TM_BOX
                self.guiMode = True
                self.gui.ShowInventory(True)
                return
            if (x,y,z) in self.gui.spawns:
                def Delete():
                    block, items = self.chunks.DigBlock(x,y,z)
                    if block:
                        self.SpawnBlockItems(x,y,z, block)
                    del self.gui.spawns[(x,y,z)]

                def SetName(name):
                    if name not in self.gui.spawns.values():
                        self.gui.spawns[(x,y,z)] = name

                self.gui.toolMode = TM_SPAWN
                self.guiMode = True
                self.gui.ShowInventory(True)
                self.gui.testEdit.Bind(SetName)
                self.gui.testEdit.BindDestroy(Delete)
                self.gui.testEdit.text = self.gui.spawns[(x,y,z)]
                return

            if (x,y,z) in self.gui.codes:
                def Delete():
                    block, items = self.chunks.DigBlock(x,y,z)
                    if block:
                        self.SpawnBlockItems(x,y,z, block)
                    del self.gui.codes[(x,y,z)]
                def SetCode(fileN):
                    self.gui.codes[(x,y,z)] = fileN
                    self.scripts[(x,y,z)] = ScriptLauncher((x,y,z))
                self.gui.toolMode = TM_CODE
                self.guiMode = True
                self.gui.ShowInventory(True)
                self.gui.testFile.Bind(SetCode)
                self.gui.testFile.BindDestroy(Delete)
                self.gui.testFile.selectedFileName = self.gui.codes[(x,y,z)]
                return

            item = self.gui.qbar[self.gui.selectedItem]
            for mob in self.mobs:
                if self.chunks.CheckCollide(x,y,z,Vector(mob.pos[0], mob.pos[1]-mob.bound[1], mob.pos[2]),mob.bound):
                    # 몹과 충돌을 한다면 바로 return한다.
                    return

            if item and item.name == "Block":
                self.sounds["Put"].play()

                mat = ViewingMatrix()
                if mat is not None:
                    if self.chunks.ModBlock(pos, dir_, 9, item.type_, self.bound, 0, mat) == -1:
                        if item.type_ == BLOCK_SPAWNER:
                            if f == 0:
                                xyz = x,y-1,z
                            elif f == 1:
                                xyz = x,y+1,z
                            elif f == 2:
                                xyz = x-1,y,z
                            elif f == 3:
                                xyz = x+1,y,z
                            elif f == 4:
                                xyz = x,y,z-1
                            elif f == 5:
                                xyz = x,y,z+1

                            self.gui.spawns[xyz] = 'Spawner_'+`len(self.gui.spawns.keys())`
                        if item.type_ == BLOCK_CODE:
                            if f == 0:
                                xyz = x,y-1,z
                            elif f == 1:
                                xyz = x,y+1,z
                            elif f == 2:
                                xyz = x-1,y,z
                            elif f == 3:
                                xyz = x+1,y,z
                            elif f == 4:
                                xyz = x,y,z-1
                            elif f == 5:
                                xyz = x,y,z+1

                            self.gui.codes[xyz] = None
                        item.count -= 1
                        if item.count == 0:
                            self.gui.qbar[self.gui.selectedItem] = ITEM_NONE


            elif item and item.name == "Item":

                if item.type_ == ITEM_CHEST:
                    dirV = self.cam1.GetDirV()
                    dx,dz = dirV.x,-dirV.z
                    if abs(dx) > abs(dz):
                        if dx < 0:
                            facing = 3
                        else:
                            facing = 2
                    else:
                        if dz < 0:
                            facing = 5
                        else:
                            facing = 4
                    installed = False

                    if f == 0:
                        pass
                    elif f == 1:
                        xyz = x,y+1,z
                    elif f == 2:
                        xyz = x-1,y,z
                    elif f == 3:
                        xyz = x+1,y,z
                    elif f == 4:
                        xyz = x,y,z-1
                    elif f == 5:
                        xyz = x,y,z+1
                    mat = ViewingMatrix()
                    if mat is not None:
                        if self.chunks.ModBlock(pos, dir_, 9, BLOCK_CHEST, self.bound, 0, mat) == -1:
                            installed = self.chunks.AddChest(xyz[0],xyz[1],xyz[2],facing)
                            if installed:
                                if item.optionalInventory:
                                    self.gui.boxes[xyz] = item.optionalInventory
                                else:
                                    self.gui.boxes[xyz] = [ITEM_NONE for i in range(60)]
                                item.count -= 1
                                if item.count == 0:
                                    self.gui.qbar[self.gui.selectedItem] = ITEM_NONE

                if item.type_ == ITEM_TORCH and self.chunks.AddTorch(x,y,z,f):
                    item.count -= 1
                    if item.count == 0:
                        self.gui.qbar[self.gui.selectedItem] = ITEM_NONE
                if item.type_ in [ITEM_STAIR, ITEM_WOODENSTAIR]:
                    dirV = self.cam1.GetDirV()
                    dx,dz = dirV.x,-dirV.z
                    if abs(dx) > abs(dz):
                        if dx < 0:
                            facing = 3
                        else:
                            facing = 2
                    else:
                        if dz < 0:
                            facing = 5
                        else:
                            facing = 4

                    if f == 0:
                        return
                    elif f == 1:
                        xyz = x,y+1,z
                    elif f == 2:
                        xyz = x-1,y,z
                    elif f == 3:
                        xyz = x+1,y,z
                    elif f == 4:
                        xyz = x,y,z-1
                    elif f == 5:
                        xyz = x,y,z+1

                    xx = xyz[0]-(xyz[0]%32)
                    yy = xyz[1]-(xyz[1]%32)
                    zz = xyz[2]-(xyz[2]%32)
                    if (xx,yy,zz) not in self.stairs:
                        self.stairs[(xx,yy,zz)] = []
                    if xyz+(facing,ITEM_STAIR) in self.stairs[(xx,yy,zz)] or xyz+(facing,ITEM_WOODENSTAIR) in self.stairs[(xx,yy,zz)]:
                        return
                    else:
                        self.stairs[(xx,yy,zz)] += [xyz+(facing,item.type_)]
                        item.count -= 1
                        if item.count == 0:
                            self.gui.qbar[self.gui.selectedItem] = ITEM_NONE

                        

        pos = self.cam1.pos
        x,y,z = pos.x, pos.y, -pos.z
        if y > 127.0:
            for zz in range(7):
                for yy in range(7):
                    for xx in range(7):
                        block, items = self.chunks.DigBlock(int(x-3+xx), int(y-3+yy), int(z-3+zz))
                        if block:
                            self.SpawnBlockItems(int(x-3+xx), int(y-3+yy), int(z-3+zz), block)
                        if items:
                            for item in items:
                                if item == ITEM_TORCH:
                                    self.gui.PutItemInInventory(Item(item, 1, color=(255,255,255), stackable=True))
                                if item == ITEM_CHEST:
                                    self.gui.PutItemInInventory(Item(item, 1, color=(255,255,255), stackable=False, inv=self.gui.boxes[(x,y,z)]))
                                    del self.gui.boxes[(x,y,z)]


    def RenderWeapon(self, x,y, color, rotate=False):
        glPushMatrix()
        texupx = (x*30.0) / 512.0
        texupy = (y*30.0) / 512.0
        x = SW-SW/3-50
        y = SH-SH/3-50
        w = 200
        h = 200
        glTranslatef(x,-y,0)
        if rotate:
            glRotatef(45, 0.0, 1.0, 1.0)
        else:
            glRotatef(45, 0.0,1.0,0.0)
        glBindTexture(GL_TEXTURE_2D, self.gui.tooltex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glBegin(GL_QUADS)
        glColor4ub(*color)

        glTexCoord2f(texupx, texupy+float(30)/512.0)
        glVertex3f(float(0), -float(0+h), 100.0)

        glTexCoord2f(texupx+float(30)/512.0, texupy+float(30)/512.0)
        glVertex3f(float(0+w), -float(0+h), 100.0)

        glTexCoord2f(texupx+float(30)/512.0, texupy)
        glVertex3f(float(0+w), -float(0), 100.0)

        glTexCoord2f(texupx, texupy)
        glVertex3f(float(0), -float(0), 100.0)
        glEnd()
        glPopMatrix()

    def RenderCrossHair(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glLineWidth(2.0)
        w = 15.0
        h = 15.0
        x = float((SW-w)/2.0)
        y = float((SH-h)/2.0)
        glBegin(GL_QUADS)
        glColor4ub(*self.chColor)
        glVertex3f(float(x), -float(y+h), 100.0)
        glVertex3f(float(x+w), -float(y+h), 100.0)
        glVertex3f(float(x+w), -float(y), 100.0)
        glVertex3f(float(x), -float(y), 100.0)
        glEnd()

        glBegin(GL_LINES)
        glColor4f(0.0,0.0,0.0,1.0)
        glVertex3f(x, -(y+h/2), 145.0)
        glVertex3f(x+w, -(y+h/2), 145.0)

        glVertex3f(x+w/2, -y, 145.0)
        glVertex3f(x+w/2, -(y+h), 145.0)
        glEnd()

        glEnable(GL_TEXTURE_2D)

    def RenderHPMP(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glLineWidth(4.0)
        x = float((SW-300)/2.0)
        y = SH-67
        width = float(self.entity.curhp)/float(self.entity.basehp)*145
        if width < 0.0:
            width = 0.0

        glBegin(GL_LINES)
        w = 145.0
        glColor4f(0.0,0.0,0.0,1.0)
        glVertex3f(x-2, -y, 145.0)
        glVertex3f(x+w+2, -y, 145.0)

        glVertex3f(x+w, -y, 145.0)
        glVertex3f(x+w, -(y+15.0), 145.0)

        glVertex3f(x+w+2, -(y+15.0), 145.0)
        glVertex3f(x-2, -(y+15.0), 145.0)

        glVertex3f(x, -(y+15.0), 145.0)
        glVertex3f(x, -y, 145.0)
        glEnd()
        glBegin(GL_QUADS)
        glColor4ub(189,45,6,255)
        glVertex3f(x, -y, 145.0)
        glVertex3f(x+width, -y, 145.0)
        glVertex3f(x+width, -(y+15.0), 145.0)
        glVertex3f(x, -(y+15.0), 145.0)
        glEnd()

        x = x + 155
        width = float(self.entity.curmp)/float(self.entity.basemp)*145
        if width < 0.0:
            width = 0.0
        w = 145.0
        glBegin(GL_LINES)
        glColor4f(0.0,0.0,0.0,1.0)
        glVertex3f(x-2, -y, 145.0)
        glVertex3f(x+w+2, -y, 145.0)

        glVertex3f(x+w, -y, 145.0)
        glVertex3f(x+w, -(y+15.0), 145.0)

        glVertex3f(x+w+2, -(y+15.0), 145.0)
        glVertex3f(x-2, -(y+15.0), 145.0)

        glVertex3f(x, -(y+15.0), 145.0)
        glVertex3f(x, -y, 145.0)
        glEnd()
        glBegin(GL_QUADS)
        glColor4ub(6,118,189,255)
        glVertex3f(x, -y, 145.0)
        glVertex3f(x+width, -y, 145.0)
        glVertex3f(x+width, -(y+15.0), 145.0)
        glVertex3f(x, -(y+15.0), 145.0)
        glEnd()


        glEnable(GL_TEXTURE_2D)

    def RenderBlockHP(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glLineWidth(3.0)
        x = float((SW-100)/2.0)
        y = float((SH-25)/2.0)
        width = float(self.blockHP/self.maxBlockHP)*100.0
        if width < 0.0:
            width = 0.0

        glBegin(GL_LINES)
        glColor4f(0.0,0.0,0.0,1.0)
        glVertex3f(x, -y, 100.0)
        glVertex3f(x+100.0, -y, 100.0)

        glVertex3f(x+100.0, -y, 100.0)
        glVertex3f(x+100.0, -(y+25.0), 100.0)

        glVertex3f(x+100.0, -(y+25.0), 100.0)
        glVertex3f(x, -(y+25.0), 100.0)

        glVertex3f(x, -(y+25.0), 100.0)
        glVertex3f(x, -y, 100.0)
        glEnd()
        glBegin(GL_QUADS)
        glColor4f(1.0,1.0,1.0,1.0)
        glVertex3f(x, -y, 100.0)
        glVertex3f(x+width, -y, 100.0)
        glVertex3f(x+width, -(y+25.0), 100.0)
        glVertex3f(x, -(y+25.0), 100.0)
        glEnd()
        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

    def GetMob(self):
        mobIntersects = []
        for mob in self.mobs:
            pos = self.cam1.pos
            pos = (pos.x, pos.y, -pos.z)
            dir_ = self.cam1.GetDirV().Normalized().MultScalar(3.0)
            dir_ = (dir_.x, dir_.y, -dir_.z)
            x,y,z = mob.pos
            min = x-mob.bound[0]/2,y-mob.bound[1],z-mob.bound[2]/2
            max = x+mob.bound[0]/2,y,z+mob.bound[2]/2
            intersects, coord = self.chunks.HitBoundingBox(min,max,pos,dir_)
            if intersects:
                mobIntersects += [(mob, coord)]
        if mobIntersects:
            pos = self.cam1.pos
            pos = Vector(pos.x, pos.y, -pos.z)
            lowest = mobIntersects[0]
            for mobcoord in mobIntersects[1:]:
                mob, coord = mobcoord
                c = Vector(*coord)
                if (c-pos).Length() < (Vector(*lowest[1])-pos).Length():
                    lowest = mobcoord
            return lowest
        return None

    def LDown(self,t,m,k):
        # 여러가지 액션 또는 땅파기 XXX
        if not self.gui.invShown:
            mob = self.GetMob()
            if mob:
                self.OnMobHit(mob, t)
                self.chColor = self.RED_CH
                return

            if self.lastBlock:
                x,y,z,f,b = self.lastBlock
                hp = 100.0
                if b == BLOCK_COALORE:
                    hp = 120.0
                if b == BLOCK_IRONORE:
                    hp = 150.0
                if b == BLOCK_SILVERORE:
                    hp = 180.0
                if b == BLOCK_GOLDORE:
                    hp = 250.0
                if b == BLOCK_DIAMONDORE:
                    hp = 500.0

                self.blockHP = hp
                self.maxBlockHP = hp
                self.prevDig = t
                self.digging = False

            self.RunScript()
    def RunScript(self):
        if self.lastBlock:
            x,y,z,f,b = self.lastBlock
            if b in [BLOCK_CODE]:
                if (x,y,z) in self.gui.codes:
                    name = self.gui.codes[(x,y,z)]
                    if name:
                        scr = self.scripts[(x,y,z)]
                        scr.code = open(name, "r").read()
                        try:
                            scr.run()
                        except:
                            import traceback
                            self.lastError = traceback.format_exc()
                            print self.lastError


    def LUp(self, t, m, k):
        self.blockHP = 100.0
        self.prevDig = t
        self.digging = False
        self.chColor = self.WHITE_CH

    def OnMobHit(self, mob, t):
        # 여기서 대화 또는 공격 XXX
        if t - self.prevAttack > self.attackDelay:
            self.prevAttack = t
            self.entity.Attack(mob[0].entity)
            self.sounds["Hit"].play()

    def OnMobRHit(self, mob, t):
        # XXX 여기서 마법 또는 상점 인터랙션?
        pass

    def GetStair(self):
        pass

    def LPressing(self, t, m, k):
        if not self.gui.invShown:
            mob = self.GetMob()
            if mob:
                self.OnMobHit(mob, t)
                self.chColor = self.RED_CH
                return

            stair = self.GetStair()
            if stair:
                # XXX HP를 깎고 스테어를 지운다.
                pass
                #self.DestroyStair()

        self.digging = False
        item = self.gui.qbar[self.gui.selectedItem]
        if not self.gui.invShown and self.lastBlock and self.prevBlock:
            x,y,z,face,block = self.lastBlock
            x2,y2,z2,face2,block2 = self.prevBlock
            if x==x2 and y==y2 and z==z2 and block == block2 and block != BLOCK_WATER:
                self.digging = True
            if t-self.prevDig > self.digDelay:
                if block in [BLOCK_GRASS, BLOCK_DIRT, BLOCK_SAND, BLOCK_LEAVES, BLOCK_GRAVEL]:
                    self.sounds["Shovel"].play()
                else:
                    self.sounds["Dig"].play()

                if block in [BLOCK_CODE, BLOCK_SPAWNER]:
                    return
                x2,y2,z2,face2,block2 = self.prevBlock
                if x==x2 and y==y2 and z==z2 and block == block2 and block != BLOCK_WATER:
                    tool = self.gui.qbar[self.gui.selectedItem]
                    if tool and tool.name == TYPE_ITEM and tool.type_ == ITEM_PICKAXE and block not in [BLOCK_GRASS, BLOCK_DIRT, BLOCK_SAND, BLOCK_LEAVES, BLOCK_GRAVEL]+[BLOCK_LOG, BLOCK_WOOD]:
                        self.blockHP -= (float(t - self.prevDig)*tool.stats[0]/100.0)
                        tool.count -= int(float(t-self.prevDig)*tool.stats[1]/100.0)
                        if tool.count <= 0:
                            self.gui.qbar[self.gui.selectedItem] = ITEM_NONE
                    elif tool and tool.name == TYPE_ITEM and tool.type_ == ITEM_AXE and block in [BLOCK_LOG, BLOCK_WOOD, BLOCK_LEAVES]:
                        self.blockHP -= (float(t - self.prevDig)*tool.stats[0]/100.0)
                        tool.count -= int(float(t-self.prevDig)*tool.stats[1]/100.0)
                        if tool.count <= 0:
                            self.gui.qbar[self.gui.selectedItem] = ITEM_NONE
                    elif tool and tool.name == TYPE_ITEM and tool.type_ == ITEM_SHOVEL and block in [BLOCK_GRASS, BLOCK_DIRT, BLOCK_SAND, BLOCK_GRAVEL]:
                        self.blockHP -= (float(t - self.prevDig)*tool.stats[0]/100.0)
                        tool.count -= int(float(t-self.prevDig)*tool.stats[1]/100.0)
                        if tool.count <= 0:
                            self.gui.qbar[self.gui.selectedItem] = ITEM_NONE
                    else:
                        self.blockHP -= (float(t - self.prevDig)*5.0/100.0)
                else:
                    if self.lastBlock:
                        x,y,z,f,b = self.lastBlock
                        hp = 100.0
                        if b == BLOCK_COALORE:
                            hp = 120.0
                        if b == BLOCK_IRONORE:
                            hp = 150.0
                        if b == BLOCK_SILVERORE:
                            hp = 180.0
                        if b == BLOCK_GOLDORE:
                            hp = 250.0
                        if b == BLOCK_DIAMONDORE:
                            hp = 500.0

                        self.blockHP = hp
                        self.maxBlockHP = hp

                if self.blockHP <= 0 and self.lastBlock:
                    if self.lastBlock:
                        x,y,z,f,b = self.lastBlock
                        hp = 100.0
                        if b == BLOCK_COALORE:
                            hp = 120.0
                        if b == BLOCK_IRONORE:
                            hp = 150.0
                        if b == BLOCK_SILVERORE:
                            hp = 180.0
                        if b == BLOCK_GOLDORE:
                            hp = 250.0
                        if b == BLOCK_DIAMONDORE:
                            hp = 500.0

                        self.blockHP = hp
                        self.maxBlockHP = hp

                    x,y,z,f,b = self.lastBlock
                    block, items = self.chunks.DigBlock(x,y,z)
                    if block:
                        if b in [BLOCK_GRASS, BLOCK_DIRT, BLOCK_SAND, BLOCK_LEAVES, BLOCK_GRAVEL]:
                            self.sounds["ShovelDone"].play()
                        else:
                            self.sounds["DigDone"].play()

                        if block == BLOCK_SPAWNER:
                            del self.gui.spawns[(x,y,z)]
                        if block == BLOCK_CODE:
                            del self.gui.codes[(x,y,z)]
                        if block == BLOCK_GRASS:
                            block = BLOCK_DIRT
                        if block not in [BLOCK_CHEST, BLOCK_IRONORE, BLOCK_COALORE, BLOCK_SILVERORE, BLOCK_GOLDORE, BLOCK_DIAMONDORE]:
                            self.SpawnBlockItems(x,y,z, block)
                        else:
                            if block == BLOCK_IRONORE:
                                self.gui.PutItemInInventory(Item(ITEM_IRON, 1, color=(107,107,107), stackable=True))
                            if block == BLOCK_COALORE:
                                self.gui.PutItemInInventory(Item(ITEM_COAL, 1, color=(60,60,60), stackable=True))
                            if block == BLOCK_SILVERORE:
                                self.gui.PutItemInInventory(Item(ITEM_SILVER, 1, color=(201,201,201), stackable=True))
                            if block == BLOCK_GOLDORE:
                                self.gui.PutItemInInventory(Item(ITEM_GOLD, 1, color=(207,207,101), stackable=True))
                            if block == BLOCK_DIAMONDORE:
                                self.gui.PutItemInInventory(Item(ITEM_DIAMOND, 1, color=(80,212,217), stackable=True))
                            #XXX: 아이템이 인벤에 넣을 공간이 없으면 땅에 드랍하는 거 구현해야함

                    if items:
                        for item in items:
                            if item == ITEM_TORCH:
                                self.gui.PutItemInInventory(Item(item, 1, color=(255,255,255), stackable=True))
                            if item == ITEM_CHEST:
                                self.gui.PutItemInInventory(Item(item, 1, color=(255,255,255), stackable=False, inv=self.gui.boxes[(x,y,z)]))
                                del self.gui.boxes[(x,y,z)]
                self.prevDig = t


    def SpawnBlockItems(self, x,y,z, block):
        self.blockItems += [(x+0.5,y+0.5,z+0.5, block, pygame.time.get_ticks(), None)]

    def CheckJump(self, y):
        if self.prevY - 0.05 <= y <= self.prevY + 0.05:
            self.canJump = True
        else:
            self.canJump = False
        self.prevY = y


    def GetNearbyItems(self):
        pos = self.cam1.pos
        x,y,z = pos.x,pos.y,-pos.z
        for item in self.blockItems[:]:
            xx,yy,zz,b,t,d = item
            if (Vector(x,y,z) - Vector(xx,yy,zz)).Length() < self.bound[1]+0.3:
                if self.gui.PutItemInInventory(Block(b, 1)):
                    self.sounds["EatItem"].play()
                    self.blockItems.remove(item)

    def ItemFall(self):
        idx = 0
        delIdx = []
        for item in self.blockItems[:]:
            xx,yy,zz,b,prevTick,d = item
            if pygame.time.get_ticks() - prevTick > 5*60*1000:
                delIdx += [idx]
            else:
                x,y,z = self.chunks.FixPos(Vector(xx,yy,zz), Vector(xx,yy-0.11,zz), (0.33,0.33,0.33))
                self.blockItems[idx] = x,y,z,b,prevTick,d
                idx += 1

        delIdx.reverse()
        for idx in delIdx:
            del self.blockItems[idx]

    def RegenTex(self,t,m,k):
        if self.regenTex:
            self.gui.inventex = texture = glGenTexturesDebug(1)
            teximg = pygame.image.tostring(self.gui.invenimg, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, self.gui.inventex)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)

            self.gui.tooltex = texture = glGenTexturesDebug(1)
            teximg = pygame.image.tostring(self.gui.toolimg, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, self.gui.tooltex)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)

            self.tex = texture = glGenTexturesDebug(1)
            image = pygame.image.load("./images/digdig/manicdigger.png")
            teximg = pygame.image.tostring(image, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)

            self.mobtex = texture = glGenTexturesDebug(1)
            image = pygame.image.load("./images/digdig/mobs.png")
            teximg = pygame.image.tostring(image, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)

            self.skyeast = texture = glGenTexturesDebug(1)
            image = pygame.image.load("./images/digdig/clouds1_east.jpg")
            teximg = pygame.image.tostring(image, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
            
            self.skywest = texture = glGenTexturesDebug(1)
            image = pygame.image.load("./images/digdig/clouds1_west.jpg")
            teximg = pygame.image.tostring(image, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
            
            self.skynorth = texture = glGenTexturesDebug(1)
            image = pygame.image.load("./images/digdig/clouds1_north.jpg")
            teximg = pygame.image.tostring(image, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
            
            self.skysouth = texture = glGenTexturesDebug(1)
            image = pygame.image.load("./images/digdig/clouds1_south.jpg")
            teximg = pygame.image.tostring(image, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
            
            self.skyup = texture = glGenTexturesDebug(1)
            image = pygame.image.load("./images/digdig/clouds1_up.jpg")
            teximg = pygame.image.tostring(image, "RGBA", 0) 
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
            

    def Render(self, t, m, k):
        for mob in self.mobs:
            mob.Tick(t,m,k)

        updateFrameCounter = 0
        fogMode=GL_EXP#GL_LINEAR# { GL_EXP, GL_EXP2, GL_LINEAR };	// Storage For Three Types Of Fog
        fogfilter= 0				#	// Which Fog To Use
        fogColor= [0.5, 0.5, 0.5, 1.0]#;		// Fog Color

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)




        if True or t - self.renderPrevTime > self.renderDelay:
            self.DoMove(t,m,k)
            self.FallOrJump(t)
            self.ItemFall()
            self.GetNearbyItems()

            self.renderPrevTime = t
            glFogi(GL_FOG_MODE, fogMode)#;		// Fog Mode
            glFogfv(GL_FOG_COLOR, fogColor)#;			// Set Fog Color
            glFogf(GL_FOG_DENSITY, 0.02)#;				// How Dense Will The Fog Be
            glHint(GL_FOG_HINT, GL_DONT_CARE)#;			// Fog Hint Value
            glFogf(GL_FOG_START, G_FAR-1.0)#;				// Fog Start Depth
            glFogf(GL_FOG_END, G_FAR+5.0)#;				// Fog End Depth
            glClearColor(132.0/255.0, 217.0/255.0, 212.0/255.0,1.0)

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            GameDrawMode()



            glDisable(GL_FOG)#;	
            dirV = self.cam1.GetDirV()
            posV = self.cam1.pos# - dirV
            self.cam1.ApplyCamera() 
            posV = Vector(posV.x, posV.y-G_FAR/10.0, posV.z)


            glDisable(GL_DEPTH_TEST)
            texID = self.skyup
            glBindTexture(GL_TEXTURE_2D, texID)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
            offsetClose = G_FAR/2
            offset = G_FAR/2.0
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(posV.x-(G_FAR-offset), posV.y+(G_FAR-offsetClose)-0.0, (-posV.z)-(G_FAR-offset))

            glTexCoord2f(1.0, 0.0)
            glVertex3f(posV.x+(G_FAR-offset), posV.y+(G_FAR-offsetClose)-0.0, (-posV.z)-(G_FAR-offset))

            glTexCoord2f(1.0, 1.0)
            glVertex3f(posV.x+(G_FAR-offset), posV.y+(G_FAR-offsetClose)-0.0, (-posV.z)+(G_FAR-offset))

            glTexCoord2f(0.0, 1.0)
            glVertex3f(posV.x-(G_FAR-offset), posV.y+(G_FAR-offsetClose)-0.0, (-posV.z)+(G_FAR-offset))
            glEnd()

            texID = self.skyeast
            glBindTexture(GL_TEXTURE_2D, texID)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
            offsetClose = G_FAR/2
            offset = G_FAR/2.0
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(posV.x+(G_FAR-offset)-0.0, posV.y-(G_FAR-offsetClose), (-posV.z)+(G_FAR-offset))

            glTexCoord2f(0.0, 0.0)
            glVertex3f(posV.x+(G_FAR-offset)-0.0, posV.y+(G_FAR-offsetClose), (-posV.z)+(G_FAR-offset))

            glTexCoord2f(1.0, 0.0)
            glVertex3f(posV.x+(G_FAR-offset)-0.0, posV.y+(G_FAR-offsetClose), (-posV.z)-(G_FAR-offset))

            glTexCoord2f(1.0, 1.0)
            glVertex3f(posV.x+(G_FAR-offset)-0.0, posV.y-(G_FAR-offsetClose), (-posV.z)-(G_FAR-offset))
            glEnd()

            texID = self.skywest
            glBindTexture(GL_TEXTURE_2D, texID)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
            offsetClose = G_FAR/2
            offset = G_FAR/2.0
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(posV.x-(G_FAR-offset)+0.0, posV.y-(G_FAR-offsetClose), (-posV.z)-(G_FAR-offset))

            glTexCoord2f(0.0, 0.0)
            glVertex3f(posV.x-(G_FAR-offset)+0.0, posV.y+(G_FAR-offsetClose), (-posV.z)-(G_FAR-offset))

            glTexCoord2f(1.0, 0.0)
            glVertex3f(posV.x-(G_FAR-offset)+0.0, posV.y+(G_FAR-offsetClose), (-posV.z)+(G_FAR-offset))

            glTexCoord2f(1.0, 1.0)
            glVertex3f(posV.x-(G_FAR-offset)+0.0, posV.y-(G_FAR-offsetClose), (-posV.z)+(G_FAR-offset))
            glEnd()

            texID = self.skynorth
            glBindTexture(GL_TEXTURE_2D, texID)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
            offsetClose = G_FAR/2
            offset = G_FAR/2.0
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(posV.x-(G_FAR-offset), posV.y-(G_FAR-offsetClose), (-posV.z)+(G_FAR-offset)-0.0)

            glTexCoord2f(0.0, 0.0)
            glVertex3f(posV.x-(G_FAR-offset), posV.y+(G_FAR-offsetClose), (-posV.z)+(G_FAR-offset)-0.0)

            glTexCoord2f(1.0, 0.0)
            glVertex3f(posV.x+(G_FAR-offset), posV.y+(G_FAR-offsetClose), (-posV.z)+(G_FAR-offset)-0.0)

            glTexCoord2f(1.0, 1.0)
            glVertex3f(posV.x+(G_FAR-offset), posV.y-(G_FAR-offsetClose), (-posV.z)+(G_FAR-offset)-0.0)
            glEnd()

            texID = self.skysouth
            glBindTexture(GL_TEXTURE_2D, texID)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
            offsetClose = G_FAR/2
            offset = G_FAR/2.0
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(posV.x+(G_FAR-offset), posV.y-(G_FAR-offsetClose), (-posV.z)-(G_FAR-offset)+0.0)

            glTexCoord2f(0.0, 0.0)
            glVertex3f(posV.x+(G_FAR-offset), posV.y+(G_FAR-offsetClose), (-posV.z)-(G_FAR-offset)+0.0)

            glTexCoord2f(1.0, 0.0)
            glVertex3f(posV.x-(G_FAR-offset), posV.y+(G_FAR-offsetClose), (-posV.z)-(G_FAR-offset)+0.0)

            glTexCoord2f(1.0, 1.0)
            glVertex3f(posV.x-(G_FAR-offset), posV.y-(G_FAR-offsetClose), (-posV.z)-(G_FAR-offset)+0.0)
            glEnd()
            glEnable(GL_DEPTH_TEST)

            glEnable(GL_FOG)#;	
            mat = ViewingMatrix()
            if mat is not None:
                frustum = NormalizeFrustum(GetFrustum(mat))
                #frustum = NormalizeFrustum(GetFrustum(mat))
                if updateFrameCounter == 0:
                    updateFrame = True
                else:
                    updateFrame = False
                for mob in self.mobs:
                    if self.chunks.CubeInFrustumPy(*(mob.pos+(0.5,frustum))):
                        mob.Render2(None, self.cam1, t) # 이것도 C로 옮기면 빨라질지도 모른다네
                        # 오픈GL을 이용하는 것보다 CPU를 이용하여 트랜슬레이트하고 한번에 그리는게 빠른가 경험상 그런듯
                        # 하지만 귀찮으니 놔두자...XXX: 나중에.

                glBindTexture(GL_TEXTURE_2D, self.tex)
                glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

                self.chunks.GenVerts(frustum, (self.cam1.pos.x, self.cam1.pos.y, -self.cam1.pos.z), updateFrame, self.gui.tooltex, self.tex)
                self.RenderStairs(frustum)
                updateFrameCounter += 0
                updateFrameCounter %= 1 # 화면이 좀 깨지기는 하지만 프레임률이 4번에 1번 하면 2배로 올라가는?
                # 8번에 1번 하면 뭐 무슨 3배로 올라가겠네 우왕 빠르당 ㅠㅠ 이걸로 가자.
                # 하지만 4번에 1번 이상은 별 효용이 없는 듯. 40배까지 올려야 2배로 올라감
                # 맵 로딩이 진짜 왕창 느리다. 옥트리 검사하는 거 때문에 진짜 느린 거 같은데.
                # 옥트리도 저장할 수 있게 해야겠다.
                # 아니? 옥트리 계산은 원래 빠른데? 음....캐슁 문제인가. 아니면, 50%만 cpu를 먹는 문제인가.
                # 하여간에 속도가 빠르고 싶다면 여기서 좀 숫자를 바꿔주면 떙이다.
                # 버퍼를 따로 써서 옥트리의 위치를 저장해서라도 옥트리의 내용을 저장해야겠다.
                #
                # 프레임 리미터도 넣자. 1초에 20번 이상은 그리지 않음!
                #
                # 옥트리 저장:
                # 128 즉 레벨 1에서는 x,y,z를 128로 나눈다.
                # 레벨 2에서는 64로 나눈다.
                # 그러면 octreeBuffer에서의 좌표가 나온다.
                # 이거를 1,8,64 등의 오프셋과 적용해서 좌표를 이용해 저장하면 된다. 로드도 같은방법
                #return
            glEnable(GL_DEPTH_TEST)

            # 32
            # 01
            # 76
            # 45
            vidx = [ (0, 1, 2, 3),  # front
                    (5, 4, 7, 6),  # back
                    (1, 5, 6, 2),  # right
                    (3, 7, 4, 0),  # left
                    (3, 2, 6, 7),  # top
                    (4, 5, 1, 0) ] # bottom    


            idx = 0
            for block in self.blockItems[:]:
                x,y,z,b,t,dList = block
                if not dList or self.regenTex:
                    dList = glGenLists(1)
                    self.blockItems[idx] = x,y,z,b,t,dList
                    glPushMatrix()
                    glTranslatef(x,y,z)
                    tex1 = 0.0, 0.0
                    tex2 = 0.0, 0.0
                    tex3 = 0.0, 0.0
                    tex4 = 0.0, 0.0
                    tex5 = 0.0, 0.0
                    tex6 = 0.0, 0.0
                    if b < len(BLOCK_TEX_COORDS):
                        texupx = (BLOCK_TEX_COORDS[b*2*3 + 0]*32.0) / 512.0
                        texupy = (BLOCK_TEX_COORDS[b*2*3 + 1]*32.0) / 512.0
                        texmidx = (BLOCK_TEX_COORDS[b*2*3 + 2]*32.0) / 512.0
                        texmidy = (BLOCK_TEX_COORDS[b*2*3 + 3]*32.0) / 512.0
                        texbotx = (BLOCK_TEX_COORDS[b*2*3 + 4]*32.0) / 512.0
                        texboty = (BLOCK_TEX_COORDS[b*2*3 + 5]*32.0) / 512.0
                        tex1 = texupx,texupy
                        tex2 = texbotx,texboty
                        tex3 = texmidx,texmidy
                        tex4 = texmidx,texmidy
                        tex5 = texmidx,texmidy
                        tex6 = texmidx,texmidy
                    glNewList(dList, GL_COMPILE)
                    DrawCube((0,0,0), (0.33,0.33,0.33), (255,255,255,200), tex1,tex2,tex3,tex4,tex5,tex6, self.tex, False, 32.0) # 텍스쳐는 아래 위 왼쪽 오른쪽 뒤 앞
                    glEndList()
                    glPopMatrix()

                else:
                    glPushMatrix()
                    glTranslatef(x,y,z)
                    glCallList(dList)
                    glPopMatrix()
                idx += 1


            pos = self.cam1.pos
            pos = Vector(pos.x, pos.y, -pos.z)
            dir_ = self.cam1.GetDirV()
            dir_ = Vector(dir_.x, dir_.y, -dir_.z)
            dir_ = dir_.Normalized()
            dir_ = dir_.MultScalar(math.sqrt(2)*9.0)
            dir_ += pos
            self.prevBlock = self.lastBlock
            mat = ViewingMatrix()
            lookPos = None
            if mat is not None:
                self.lastBlock = lookPos = self.chunks.LookAtBlock(pos, dir_, 7, self.bound, mat)#self.difY)

            if lookPos and lookPos[4] != BLOCK_WATER:
                x,y,z,face,block = lookPos
                glLineWidth(6.0)
                #glDisable(GL_DEPTH_TEST)
                glDisable(GL_TEXTURE_2D)
                glBegin(GL_LINES)
                glColor4f(1.0, 0.5, 0.5, 0.8)
                if face == 0:
                    y -= 0.01
                    glVertex3f(x, y, z)
                    glVertex3f(x+1.0, y, z)

                    glVertex3f(x+1.0, y, z)
                    glVertex3f(x+1.0, y, z+1.0)

                    glVertex3f(x+1.0, y, z+1.0)
                    glVertex3f(x, y, z+1.0)

                    glVertex3f(x, y, z+1.0)
                    glVertex3f(x, y, z)
                if face == 1:
                    y += 0.01
                    glVertex3f(x, y+1.0, z)
                    glVertex3f(x+1.0, y+1.0, z)

                    glVertex3f(x+1.0, y+1.0, z)
                    glVertex3f(x+1.0, y+1.0, z+1.0)

                    glVertex3f(x+1.0, y+1.0, z+1.0)
                    glVertex3f(x, y+1.0, z+1.0)

                    glVertex3f(x, y+1.0, z+1.0)
                    glVertex3f(x, y+1.0, z)
                if face == 2:
                    x -= 0.01
                    glVertex3f(x, y, z)
                    glVertex3f(x, y+1.0, z)

                    glVertex3f(x, y+1.0, z)
                    glVertex3f(x, y+1.0, z+1.0)

                    glVertex3f(x, y+1.0, z+1.0)
                    glVertex3f(x, y, z+1.0)

                    glVertex3f(x, y, z+1.0)
                    glVertex3f(x, y, z)
                if face == 3:
                    x += 0.01
                    glVertex3f(x+1.0, y, z)
                    glVertex3f(x+1.0, y+1.0, z)

                    glVertex3f(x+1.0, y+1.0, z)
                    glVertex3f(x+1.0, y+1.0, z+1.0)

                    glVertex3f(x+1.0, y+1.0, z+1.0)
                    glVertex3f(x+1.0, y, z+1.0)

                    glVertex3f(x+1.0, y, z+1.0)
                    glVertex3f(x+1.0, y, z)
                if face == 4:
                    z -= 0.01
                    glVertex3f(x,y,z)
                    glVertex3f(x+1.0,y,z)

                    glVertex3f(x+1.0,y,z)
                    glVertex3f(x+1.0,y+1.0,z)

                    glVertex3f(x+1.0,y+1.0,z)
                    glVertex3f(x,y+1.0,z)

                    glVertex3f(x,y+1.0,z)
                    glVertex3f(x,y,z)
                if face == 5:
                    z += 0.01
                    glVertex3f(x,y,z+1.0)
                    glVertex3f(x+1.0,y,z+1.0)

                    glVertex3f(x+1.0,y,z+1.0)
                    glVertex3f(x+1.0,y+1.0,z+1.0)

                    glVertex3f(x+1.0,y+1.0,z+1.0)
                    glVertex3f(x,y+1.0,z+1.0)

                    glVertex3f(x,y+1.0,z+1.0)
                    glVertex3f(x,y,z+1.0)
                glEnd()
                glEnable(GL_TEXTURE_2D)
                glEnable(GL_DEPTH_TEST)



            GUIDrawMode()
            glDisable(GL_FOG)#;	
            if self.chunks.InWater(self.cam1.pos.x, self.cam1.pos.y, -self.cam1.pos.z):
                glDisable(GL_TEXTURE_2D)
                glBegin(GL_QUADS)
                glColor4ub(23,92,219, 100)
                glVertex3f(0.0, -float(SH), 100.0)
                glVertex3f(float(SW), -float(SH), 100.0)
                glVertex3f(float(SW), 0.0, 100.0)
                glVertex3f(0.0, 0.0, 100.0)
                glEnd()
                glEnable(GL_TEXTURE_2D)

            """
            glBindTexture(GL_TEXTURE_2D, self.guitex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
            #GUISt.RenderGUI()

            glBegin(GL_QUADS)
            glTexCoord2f(0.0, float(512)/512.0)
            glVertex3f(0.0, -float(512), 100.0)
            glTexCoord2f(float(512)/512.0, float(512)/512.0)
            glVertex3f(float(512), -float(512), 100.0)
            glTexCoord2f(float(512)/512.0, 0.0)
            glVertex3f(float(512), 0.0, 100.0)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(0.0, 0.0, 100.0)
            """
            """
            glTexCoord2f(0.0, float(SH)/1024.0)
            glVertex3f(0.0, -float(SH), 100.0)
            glTexCoord2f(float(SW)/1024.0, float(SH)/1024.0)
            glVertex3f(float(SW), -float(SH), 100.0)
            glTexCoord2f(float(SW)/1024.0, 0.0)
            glVertex3f(float(SW), 0.0, 100.0)
            glTexCoord2f(0.0, 0.0)
            glVertex3f(0.0, 0.0, 100.0)
            """
            """
            glColor3f(1.0, 1.0, 0.0)
            glVertex3f(-10.0, 0.0, -10.0)
            glVertex3f(10.0, 0.0, -10.0)
            glVertex3f(10.0, 0.0, 10.0)
            glVertex3f(-10.0, 0.0, 10.0)
            glEnd()
            """
            #self.RenderWeapon(0,1,(255,0,0,255), False)
            self.RenderCrossHair()
            self.RenderHPMP()
            self.gui.Render(t, m, k)
            self.gui.RenderNumber(int(self.fps.GetFPS()), 0, 0)
            if self.digging:
                self.RenderBlockHP()
            pygame.display.flip()
                    


    def KeyTest(self, t, m, k):
        self.show = not self.show
        self.housing.Show(self.show)
    def OpenInventory(self, t, m, k):
        if k.pressedKey == K_i and not self.guiMode:
            self.guiMode = not self.guiMode
            self.gui.toolMode = TM_TOOL
            self.gui.ShowInventory(self.guiMode)
        elif k.pressedKey == K_c and not self.guiMode:
            self.guiMode = not self.guiMode
            self.gui.toolMode = TM_CHAR
            self.gui.ShowInventory(self.guiMode)
        elif k.pressedKey == K_e and not self.guiMode:
            self.guiMode = not self.guiMode
            self.gui.toolMode = TM_EQ
            self.gui.ShowInventory(self.guiMode)
        elif k.pressedKey == K_ESCAPE:
            self.guiMode = False
            self.gui.ShowInventory(self.guiMode)

    def GenId(self):
        r = self.id
        self.id += 1
        return r
    def Run(self):
        global g_Textures
        self.regenTex = False
        pygame.init()
        self.sounds = {
                "Dig": pygame.mixer.Sound("./images/digdig/thump.wav"),
                "Shovel": pygame.mixer.Sound("./images/digdig/shovel.wav"),
                "Put": pygame.mixer.Sound("./images/digdig/putblock.wav"),
                "DigDone": pygame.mixer.Sound("./images/digdig/digdone.wav"),
                "ShovelDone": pygame.mixer.Sound("./images/digdig/shoveldone.wav"),
                "EatItem": pygame.mixer.Sound("./images/digdig/eatitem.wav"),
                "Hit": pygame.mixer.Sound("./images/digdig/hitmelee.wav"),
                "Hit2": pygame.mixer.Sound("./images/digdig/hit2.wav"),
                }
        for sound in self.sounds.itervalues():
            sound.set_volume(0.8)
        isFullScreen = 0#FULLSCREEN
        screen = pygame.display.set_mode((SW,SH), HWSURFACE|OPENGL|DOUBLEBUF|isFullScreen)#|FULLSCREEN)
        pygame.mouse.set_cursor(*pygame.cursors.load_xbm("./images/digdig/cursor.xbm", "./images/digdig/cursor-mask.xbm"))
        
        resize(SW,SH)
        init()
        self.WHITE_CH = (255,255,255,160)
        self.RED_CH = (189,45,6,160)
        self.BLUE_CH = (6,118,189,160)
        self.chColor = self.WHITE_CH

        glViewport(0, 0, SW, SH)
        self.cam1 = Camera()
        self.cam1.pos.y = 90
        emgr = EventManager()
        self.fps = fps = FPS()
        emgr.BindLPressing(self.LPressing)
        emgr.BindLDown(self.LDown)
        emgr.BindLUp(self.LUp)
        emgr.BindRDown(self.RDown)
        emgr.BindRUp(self.RUp)
        emgr.BindRPressing(self.RPressing)
        emgr.BindKeyDown(self.OpenInventory)
        #emgr.BindTick(self.DoMove)
        emgr.BindMotion(self.DoCam)
        emgr.BindTick(self.Render)
        emgr.BindTick(self.RegenTex)
        self.font = pygame.font.Font("./fonts/NanumGothicBold.ttf", 19)
        self.id = 0
        self.entity = FightingEntity(self.GenId(), "Player", self.cam1.pos, {"hp": 100, "mp": 100, "str": 5, "dex": 5, "int": 5})
        # 스탯등을 올릴 때 처음엔 네 대 때려야 죽을게 3대 때리면 죽고 싸우다보면 2대 때리면 죽고 이런식으로
        # 좀 뭔가 레벨업 하듯이 할맛 나게

        
        #gui = GUI()
        #caret = Caret()
        #self.inventoryV = VisibilitySet()
        #cbg = InvenBG((0,30,500,450))
        #self.inventoryV.AddBG(cbg)
        #self.inventoryV.Show(False)
        #cbg = QBBG((0,450,300,30))
        self.gui = DigDigGUI()
        self.scripts = {}
        for coord in self.gui.codes:
            self.scripts[coord] = ScriptLauncher(coord)
        pygame.mixer.music.load("./sounds/digdigtheme.wav")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)
        def prr():
            print 'aa'
        """
        but = Button(prr, u"테스트", (0,40,0,0))
        self.housing = VisibilitySet()
        self.housing.Add(but)
        self.housing.Show(False)
        emgr.BindKeyDown(self.KeyTest)
        """
        """
        but = Button(house.SetSE, u"남동", (0,40,0,0))
        self.housing.Add(but)
        but = Button(house.SetSW, u"남서", (0,80,0,0))
        self.housing.Add(but)
        but = Button(house.SetFloor, u"바닥", (0,120,0,0))
        self.housing.Add(but)
        self.housing.Show(False)
        """
        skin = [
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 0*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 0*64.0/512.0),
            (1*64.0/512.0, 0*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 1*64.0/512.0)],
            [(0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (0*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 1*64.0/512.0),
            (1*64.0/512.0, 1*64.0/512.0)]]


        """
        entity = FightingEntity(self.GenId(), "Mob1", self.cam1.pos, {"hp": 100, "mp": 100, "str": 5, "dex": 5, "int": 5})
        self.mobs = [MobGL((0.0,0.0,0.0), self.bound, skin, MOB_SKELETON, (200,200,200,255), entity) for i in range(1)]
        """
        entity = FightingEntity(self.GenId(), "Mob1", self.cam1.pos, {"hp": 100, "mp": 100, "str": 5, "dex": 5, "int": 5})
        self.mobs = []
        #self.mobs = [MobGL((0.0,0.0,0.0), self.bound, skin, MOB_SKELETON, (200,200,200,255), entity) for i in range(1)]
        try:
            self.stairs = pickle.load(open("./map/stairs.pkl", "r"))
        except:
            self.stairs = {} # 32x32x32의 청크수준의 좌표를 담음
        self.stairsDL = {}
        
        pygame.mouse.set_visible(False)

        import chunkhandler
        self.chunks = chunks = chunkhandler.Chunks()
        done = False

        glEnable(GL_CULL_FACE)
        self.tex = texture = glGenTexturesDebug(1)
        glEnable(GL_TEXTURE_2D)
        image = pygame.image.load("./images/digdig/manicdigger.png")
        #teximg = pygame.surfarray.array3d(image)
        teximg = pygame.image.tostring(image, "RGBA", 0) 
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST)# Linear Filtering
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST)
        #glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)# Linear Filtering
        #glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)# Linear Filtering

        
        self.mobtex = texture = glGenTexturesDebug(1)
        image = pygame.image.load("./images/digdig/mobs.png")
        teximg = pygame.image.tostring(image, "RGBA", 0) 
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST)# Linear Filtering
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST)

        self.skyeast = texture = glGenTexturesDebug(1)
        image = pygame.image.load("./images/digdig/clouds1_east.jpg")
        teximg = pygame.image.tostring(image, "RGBA", 0) 
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
        
        self.skywest = texture = glGenTexturesDebug(1)
        image = pygame.image.load("./images/digdig/clouds1_west.jpg")
        teximg = pygame.image.tostring(image, "RGBA", 0) 
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
        
        self.skynorth = texture = glGenTexturesDebug(1)
        image = pygame.image.load("./images/digdig/clouds1_north.jpg")
        teximg = pygame.image.tostring(image, "RGBA", 0) 
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
        
        self.skysouth = texture = glGenTexturesDebug(1)
        image = pygame.image.load("./images/digdig/clouds1_south.jpg")
        teximg = pygame.image.tostring(image, "RGBA", 0) 
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)
        
        self.skyup = texture = glGenTexturesDebug(1)
        image = pygame.image.load("./images/digdig/clouds1_up.jpg")
        teximg = pygame.image.tostring(image, "RGBA", 0) 
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximg)



        glMatrixMode(GL_MODELVIEW)

        try:
            self.cam1.pos = pickle.load(open("./map/pos.pkl", "r"))
        except:
            self.cam1.pos.y = 64.0+21.0;
        
        p = self.cam1.pos+(self.cam1.GetDirV().MultScalar(2.0))
        idx = 0
        for mob in self.mobs:
            mob.pos = p.x+idx*1.0, p.y, (-p.z)
            idx += 1
        
        self.chunks.SaveRegion("test", (64,0,64), (127+64,127,127+64))
        while not done:
            fps.Start()
            for e in pygame.event.get():
                if e.type is QUIT: 
                    done = True
                elif e.type is KEYDOWN and e.mod & KMOD_LALT and e.key == K_F4:
                    done = True
                elif e.type is MOUSEMOTION:
                    pass
                elif e.type is MOUSEBUTTONDOWN:
                    pass
                elif e.type is MOUSEBUTTONUP:
                    pass
                elif e.type == ACTIVEEVENT and e.gain == 1:
                    screen = pygame.display.set_mode((SW,SH), HWSURFACE|OPENGL|DOUBLEBUF|isFullScreen)#|FULLSCREEN) # SDL의 제한 때문에 어쩔 수가 없다.
                    self.regenTex = True
                    g_Textures = []
                    pass
                emgr.Event(e)
            emgr.Tick()
            self.gui.invShown = self.gui.setInvShown
            self.regenTex = False
            fps.End()
            #print fps.GetFPS()
        self.chunks.Save()
        pickle.dump(self.cam1.pos, open("./map/pos.pkl", "w"))
        pickle.dump(self.gui.inventory, open("./map/inv.pkl", "w"))
        pickle.dump(self.gui.qbar, open("./map/qb.pkl", "w"))
        pickle.dump(self.gui.boxes, open("./map/chests.pkl", "w"))
        pickle.dump(self.gui.codes, open("./map/codes.pkl", "w"))
        pickle.dump(self.gui.spawns, open("./map/spawns.pkl", "w"))
        pickle.dump(self.gui.eqs, open("./map/eqs.pkl", "w"))
        pickle.dump(self.stairs, open("./map/stairs.pkl", "w"))



if __name__ == '__main__':
    def run():
        app = DigDigApp()
        app.Run()
    run()
    #chunkhandler.Test()
    """
    v1 = Vector(-1.1,0.1,-0.1)
    v2 = Vector(0.1,0.1,1.1)
    print v1.Dot(v2)
    """


"""
ㅋㅋㅋㅋㅋㅋㅋㅋ 마인크래프트 클론을 만들어서 드워프 포트리스처럼 만들자.
기본적으로 서버가 있고 무한맵.
음.... 맵 데이터를 DB에 저장하는가?
걍 리스트로 해도 졸라 느릴텐데, DB에 하면 더 느리겠지?
3차원인데 100000x100000x100000 막 이럴텐데 말이지.
Surface만 읽어올려고 해도 현재 뷰포인트에서 그걸 다 가져오는 알고리즘만 해도 엄청 느릴 것 같다.
그 부분은 Pyrex로?

일단 프러스텀 영역에 맞는 타일들만 가져와서
타일의 각 면이 다른 벽과 인접하지 않았다면 일단 그리고, 인접한다면 그 면은 뺀다.
면 단위로 한다.
거기서 다시 Z소팅을 통해 비지블 영역만 가져와야 한다. -- 이건 생략 가능. 단지 벽 뒷면이라던가 이런 부분은 그릴 필요가 없는데... 괜히 느리지 않을까?
쿼드 중에서 첫번째 vertex와 2번째 버텍스를 검사해서 플레이어를 향하지 않는다면 뺀다. Pyrex로.

- 프러스텀에 맞는 모든 쳥크에 대해(굉장히 많을 수 있고 맵 전체가 될 수 있을까? FAR PLANE이 있으니까 그거에 걸리겠지 뭐.
- 6개의 각 면에 인접하는 벽이 없으면 렌더리스트에 추가(제일 느림)
- 시계방향 검사 컬링(보이는 영역을 현재 coord로 cpu에서 트랜슬레이트 해야하지만 그래도 한다.)
- 타일링이 가능한가? 2방향으로 일렬로 쭉 검사. 2방향 중 평균 타일링이 가장 많이 되는 부분을 골라서 타일링함. GL_REPEAT으로 구현

즉 현재 보이는 타일만 가져오기 위해 이걸 다 해야한다는....
최적화 가능한 장소:
    땅이 예를들어 100x100x100으로 속에 빈 공간이 하나도 없을 때에는? 이걸 다 검사하면 진짜 느릴걸????
    100x100x100x6번을 검사해야 하는데 그럼 이건 완전 600만번을 검사해야 한다. 그러지 말고
    16x16x16 또는 일정한 숫자를 한개의 트리로 만들어서 미리 인접영역에 대한 검사를 해두고... 맵 생성시에
    실시간으로 업뎃한다.
    음...... 옥트리를 만들어서 속에 빈 공간과 인접한 영역에도 빈 공간/물타일 등의 투명타일이 하나도 없는 그런 트리는 아예 검사도 하지 않게 하자.
    또한 전체가 물타일인 트리 역시 주변이 다 물이라면 검사할 필요가 없고 뭐 이렇다.



Y축 갯수는 128층으로 제한한다. 땅 기준 평균 위로 48층, 아래로 80층
X,Z축은 그냥 맵을 돌아다닐 때 마다 생성된다. 자연동굴 기능은 아직 넣지 않는다.
맵이 일정 이상 생성되고 플레이어가 한 번도 본 적이 없는 땅 영역 안에 자연동굴을 넣어야 할텐데. 산도 이어서 만들어야하고.
음.... 그렇다면 아예 산, 강, 폭포 이런걸 기준으로 생성하고 타일만 그걸 기준으로 생성하도록 하면 되겠군?

1024x768해상도에서 최악의 시나리오는 2x2픽셀당 블럭 한개. 그러면... 프러스텀 안에 거의 512x512x512의 갯수가 있다.
그러면 이게 16x16x16으로 되어있다고 치고 그럼 32768개의 청크를 검사해야 한다. 하지만 이건 진짜 최악의 경우고 파 플레인이 있으니까
32x32x4 정도 해서 4096개 정도 검사.
음....아주 최악의 경우 보통 8만개의 트라이앵글이 그려지지 않을까 예상.
음...pygame으로 OPENGL로 하자. Ogre쓸려니까 뒤질거같음;
-------------------
음... 복잡한 GUI는 필요가 없다. 걍 이미지 출력으로 끝내자. 한글입출력은 간단함....
-------
http://www.crownandcutlass.com/features/technicaldetails/frustum.html
-------
일단, 옥트리의 각 꼭지점중 하나가 프러스텀 안에 있으면 프러스텀 안에 있는 것.
음....... 그런데 옥트리가 프러스텀보다 크다면?

프러스텀:
    꼭지점들
    선들
    면들

옥트리:
    꼭지점들
    선들
    면들

기본적으로 옥트리가 프러스텀을 완전히 감싸고 있을 경우 모든 차일드를 검사해서 프러스텀 바깥에 있는 걸 추려내야 한다.
프러스텀 바깥에 있는 거만 검사하는거다.
프러스텀 바깥에 있는 거는 어떻게 검사하나?
노드의 각 선이 완전히 프러스텀 바깥에 있고, 노드가 프러스텀을 완전히 감싸고 있지 않을 경우, 이건 밖에 있는거다. 나머지는 안에있는 것.

즉, 노드가 프러스텀을 완전히 감싸는지 검사
아니라면 노드가 프러스텀 밖에 있는지를 검사
아니라면 노드가 완전히 프러스텀 안에 있는지를 검사 --> 다그림
아니라면 노드가 반정도 프러스텀 안에 있는지 검사 --> 차일드를 검사하고 최종 차일드라면 다그림


필요한 수학도구: 프러스텀 안에 노드가 있는지, 걸치는지 검사하는 루틴
노드 안에 프러스텀이 완벽하게 감싸고 있는지 검사하는 루틴
프러스텀 밖에 노드가 있는지 검사하는 루틴

플레인만으로 볼륨안밖을 검사할 수 있을 것 같다. 아..... 각 프러스텀 플레인의 면으로 안밖을 결정하고, 만약 노드의 모든 면선점이 완벽하게 밖에 있다면
밖에 있는거고
아니라면 다음 플레인으로 검사해서 완벽하게 밖에있다 그러면 또 밖에 있는거고
최소 한 프러스텀플레인 / 최대 모든 프러스텀플레인으로 검사해서 완벽하게 밖에 있는 게 아니면 그리는 거다.
점이 밖에 있다면 면이 밖에 있는 거다. 그럼 점이 플레인의 +영역에 있나 -영역에 있나만 검사하면 된다.


	C.x = (A.y * B.z) - (A.z * B.y);
	C.y = (A.z * B.x) - (A.x * B.z);
	C.z = (A.x * B.y) - (A.y * a.x);
	v.x = point2.x - point1.x;
	v.y = point2.y - point1.y;
	v.z = point2.z - point1.z;

---------------------
음....... 
----------
GUI. GUI는 블릿으로 한다. 텍스쳐 4장에다가 그린 후 화면에 쿼드 4개로 Ortho로 뿌린다.
----------
이제 블럭 충돌검사, 땅파기를 구현한다.
chunkdata로 좌표 주변 4x4x4를 가져와서 충돌검사
팔 때마다 Octree변경 잘해야함
------
음 나는 봤음 블럭 뭔가 가리킨쪽에 안쌓이고 오른쪽끝자락에 쌓이는 버그를.
다시 해봣는데 안나타나지만 이런 버그가 있긴 있었다는 걸 기록해두자능.
음 내 생각에 아마 마우스가 잠깐 튀어서 그랬을 수도 있다고 생각되지만... 그건 증거없는 희망적인 생각일 수도 있고;;

아. 마우스 피킹하는 레이가 화면상에서는 내 앞에 있지만, 실제로는 레이는 블럭 좌표내에 Frustum을 적용하지 않은 좌표에 있다. 그러므로
그 레이가 실제 어떻게 생겼는지는 뭐 잘 모르지.
-----------------------------------------------
음 버텍스 라이팅을 할 때 어떻게 해야하나.
라잇 소스가 카메라 윗쪽 태양이라면 낮이면 어디에 가도 환하다 일단.
ColorPointer로 라이팅을 cpu로 계산?
아.....노멀이 있어야 라이팅이 되는군하;;
----------------
--------
이제 GUI를 하자.
---------
프로그램으로 함정, 기계, 머신건 도어 등등 여러가지를 만들 수 있다.
------
GUI했으니 이제 맵생성을 하고 파는걸 하고 여러블럭을 한다.
==0 또는 !=0이런것들 전부 제대로 바꿔줘야 한다.
-------------
만드는 거에만 집중하고 뭐 몬스터 이런 건 그냥 하지 않는다.
서로 싸우는 거는 기계 등을 진짜 강화시킨다.
-----------------------
알파값이 있는 face들은 따로 모아서 나중에 렌더링 해야한다.
----------
인벤토리 done
맵생성 done
아이템 half
토치와 라이팅
물이나 라바 흐르기
땅파기 구현 half
코드/기계
나무같은거 자라는거
몹, 전투 등등

물 흐르기는 옥트리에 contains_water 플래그값을 넣어야 한다.

전투는 커스텀 디펜스처럼 커스텀 스킬을 부여 가능.
---------------
"""
# 청크 쿼드트리, 청크 메모리가 꽉차면 프리하고 다른거 로드하는기능 꼭 넣기 XXX:
"""
한칸 Y값 차이나는 거 계단ㅁ 없어도 그냥 점프 안해도 걸어가면 올라갈 수 있게.
+1.0을 y에 해서 충돌검사에 안걸리면 y+1.0으로 고쳐서 하도록 한다.
------------
타일 채울 때 땅속에 grass가 없게 한다.
현재 채우는 땅의 바로 밑이라던가 그런데를 검사해서 grass면 없앤다던가
64이상의 타일을 다 검사해서 grass면 dirt로 바꾸고 이러면 된다.
-----------
땅팔때 애니메이션 말고 그냥 체력바를 표시하자.
현재 선택된 블럭을 하이라이트하는건 해야하는데 그거는 GL_LINE으로 할까 depth test 끄고
-------------
물속에서는 즉 물 블럭은 pick할지 안할지 옵션에서 조절해서 버켓인 경우 그리고 물속이 아닌 경우 물을 파고 그러게 한다.
--------
아이템이 나오면 일단 막 밑으로 떨어지고 옆으로도 살짝 튕기는 그런 효과가 있다가 땅에 완전히 떨어지면 static목록에 들어가게 된다.

Worldobject를 만들고
위치를 지정하고
그리면 땡

간단하게 하려면 아예 맵상에 존재할 수 있는 블럭 오브젝트를 제한하고 그 수가 넘...이건 접자. 그냥 그리면 됨.;
하지만 제한을 하기는 해야하고 시간이 다되면 지우는것도 해야한다.
땅에 버린 아이템은 저장되지 않는다.

이제 아이템 먹는거 까지 대충 했으니까 인벤토리에 아이템을 표시하고 클릭하는 그걸 구현한다. 전에 구현했었지 아마.....

인벤토리 /퀵바 드래그드랍을 구현
------------
자주쓰이는 글자들을 캐슁하는 방법도 좋다.
--------------
이제 아이템 제작 창.
그냥 특별히 제작 툴이 없어도 리스트에서 뭐든 만들 수 있도록 한다.
뭘 녹이고 이러는 거만 포지 옆에서 하도록.
나중에 기계로 만들면 대량생산이 가능하고...?!
-----------------------
이제 토치를 만들자.

옥트리 안에다가 토치를 넣어야 한다.
그리고 렌더링시 주변 4 옥트리를?.....음.
그러지 말고 chunk버퍼처럼 버퍼로 해서 주변 몇개를 쉽게 얻어올 수 있도록 한다.
대신 한칸한칸 하는게 아니라 8x8x8을 하나로 해서 그 안에다가 좌표와 함께 넣고 뭐 이런다.
그리고 주변 몇개를 얻어올까? 주변.... 꽤 많이 얻어와야할거같은데. 8x8x8짜리를 3개씩 얻어오면 16x16x16안에 있는 조명으로 밝히기를 하는 조명 할 수 있다.
-----
다하면 채팅기능. 명령어기능. sqlite를 이용해서 데이터를 저장하는 기능. 클래스 변경하면 호환성 없는 피클은 그만~
음 텍스트 에어리어는 넣었다. 자자.....
------------------------
이제 기계 만들어볼까?
텍스트 에디터는.. 하지 말고
파일 브라우져를 만들어서 스크립트 폴더에 스크립트를 넣으면 그 스크립트를 실행할 수 있게 한다. 루아로 할까 파이싼...파이썬으로 하자.
필드 아이템은...아이템은... sqlite에 넣자.;;;;
torch랑 chest는....그냥 다 만들었으니 놔두고 나머지는 앞으로는 sqlite ㅠㅠ
-----
mutex.lock(function, argument)
Execute function(argument), unless the mutex is locked. In the case it is locked, place the function and argument on the queue. See unlock() for explanation of when function(argument) is executed in that case.
mutex.unlock()
Unlock the 
---------
배선하기: 현재 보는 방향으로 세로로 뿌리게 한다. 다른 배선의 위치는 검사하지 않음. 알아서 해야함.
세로로 뿌리고 좌측으로 ㄱ인지 역기역인지만 결정하게 한다. ㄴ이나 역 ㄴ을 할 때는 반대방향에서 하면 됨.
아 전부 다 ㄱ자로 해도 되네? 동서남북인지만 알면....
땅에 까는건 일자 기역자 다 되고
면 2,3,4,5 옆면에 까는건 일자만 현재 방향에서 세로로 된다.
선이 겹칠 때 땅속으로 파고 들어가서 아...그럴 필요가 없는데. 그냥 겹치게 해도 원하는 효과 나올 듯.
걍 산 위에서 아래로 연결할 때를 대비해서 이렇게 한다.
-----------
배선하기
코드를 실행시에 8방향을 검사해서(코드블럭 자체에 붙어있는 배선은 건들지 않음, 하지만 언덕 위에서 연결하는 걸
지원하기 위해 현재높이 4방향, 한칸 위 높이 4방향을 검사함)
각각의 이 코드를 향하고 있는 배선을 쭉 따라가서
가장 마지막에 연결된 배선이 아닌 기계와 연결하고
그게 뭔지를 알아본다.
cpu, power따위는 없애고 코드블럭만 쓴다.
코드블럭은 OnHit(주먹으로 침, 화살등으로 쏨)으로 액티베이트 되거나
일정 거리 이상으로 사람이 들어오면 작동하게 하고
?블럭은 범용으로 여러가지로 쓰이게 된다.

나중에 스킨을 입혀서 문이나 뭐 그런걸로 변신하도록 하게도 한다.

Spanwer를 변수처럼 써서 그냥 coord를 대표하는 그런걸로 쓴다. 이름을 붙이거나 좌표를 써야함
처음엔 자동으로 이름이 붙어짐
게임상에 푯말 글자 출력도 막 네온사인처럼 움직이는 글자 할 수 있음!
------------
일단 아이템이 땅에 떨어지는 걸 구현한다.
스포너 위에 상자를 올리면 상자에 들어있는 아이템이 푝푝 튀어나옴? +_+
------------
자 이제....잡을 수 있는 몹과 전투 캐릭터를 구현.
너무 복잡하게 하지 말고...딱 디아2 정도만..-_- 하자. 진짜~~~어렵겠는데
몹은 그냥.... 일직선으로 캐릭터의 방향으로 점프를 하면서 달려오기만 한다. 길찾기 이런거 없음 막히면 못옴; 막혀도 오는 건 벽타고 오는거 뿐임;;
몹은

인간형은 사각형 머리 몸통 팔2개 다리2개 6개의 큐브로 구현. 큐브를 회전시키는 걸로 애니메이션을 구현
몹을 그렸는데........ 느린데? -_-
C로 그리고 pyrex에서 GL콜을 할까? 큐븐데 차이가 있을지....
큐브들을 텍스코드랑 같이 저장해두고
그걸 몹의 수와 몹의 애니메이션 상태를 따라 회전따로 다하고 뭐 이럴까
일단 pyrex로 버텍스 포인터로 해보고 느린지 보도록 하자.
---------
코드로 플레이어가 몹을 발견하거나 했을 때의 매크로도 짤 수 있도록.
뭐 매크로로 블럭을 짠다던가 건물을 짓는 것도 가능?
-----------
맵상의 아이템이나 몹들을 chunk9개 안에 있는 것들만 업데이트 한다.
싱글플레이어에서는 마스터 맵을 따로 저장하고 세이브파일로 마스터맵을 복사해서 플레이하고 세이브하게 한다.
몹 위에 체력바 그리기done
플레이어의 체력바 그리기done
-----------
블럭으로 몹을 가릴 수 있다. 충돌검사를 Python으로 가져온다. - DONE
----------
이제 일정 Range안에 들어오면 OnSpawnerRange 코드를 실행 하는 것과
몹이나 NPC를 좌측클릭하거나 우측클릭하면 액션이 실행되는 걸 하자.
우측클릭은 대화 좌측클릭은 상점이나 뭐 그런가? 우클릭은 대화 좌클릭은 공격을 하나.

일단 Hit으로 스폰 Hit하면 이벤트 파이어.
----------
아 스포너는 인터랙션이 없고 출력장치일 뿐이다.
코드가 인터랙션 다 받고 그런다.
코드 대신 뭐 스위치라던가 밟는 패널 이런거 전부 코드블럭이 모양만 다른 것이다.
코드 = 인풋+함수
스포너 = 아웃풋
스포너 대신 여러가지 아웃풋이 가능한 기능이 여러가지인 블럭들이나 횃불같은 아이템을 넣는다.

루프가 없으니 뮤텍스 쓸 필요도 없겠네;
---------------
몹이 많으니까 느리므로 최적화를 하던가
몹의 숫자를 최소화 한다! 1:1전투가 길고 리워드가 많으면 된다.
---------------
이제 전투를 구현한다. 아이템도 구현한다. 아이템 제작도 한다. 스킬도 구현한다.
---------
무기
방패
모자
몸통
장갑
신발
목걸이
반지

0, 200

26,228
26,262
26,296
26,330

250,228
250,262
250,296
250,330
---------------
주변 보더가 1인 글자를 그릴 수 있을까?
음 좌측 왼쪽, 왼쪽위 왼쪽 아래로 한번씩 복사하고
이런식으로 9방향으로 복사하면
대충 나오지 않을까.;; 
오 되넹;; (....)
------
엘레베이터, 자동차, 열차, 탈 수 있는 날아다니는 비행체 등등을 만들 수 있도록.
포탈은 없고 매우 빠른 열차를 이용할 수 있도록 하자.

심시티나 캐피탈리즘 같은 요소를 넣어? (....) 상점운영이 되도록 음....


네온사인을 만들기 위해 코드로 컬러를 바꿀 수 있는 이름 붙일 수 있는 블럭을 넣는다?
-----------------------------------------
일단..... 캐슁. 캐슁이 되야한다. 캐슁을 잘할 수 있는 방법이 없을까?
-------------------------------------------------------------------
6면이 다 가려진 건 한 번 뚫릴 때 까지 그려질 염려가 없다.
그러므로 뚫렸을 때에만 뚫린 부분에만 업뎃을 하면 된다.
반면, terrain부분은 계속 그려지고 계속 업뎃이 된다.
실시간으로 load/save를 해도 되니까 현재 뷰포인트를 중심으로 일정 박스 안에 있는 6면이 안가려진 놈들은 다 버텍스 캐쉬에 두고
한 번 캐쉬가 만들어지면 움직일 때 마다 안보이게 된 부분을 캐쉬에서 없애고 보이게 된 부분을 새롭게 추가하고 이러면 될 것 같다.
음 안보이게 되는 부분이라던가 보이게 되는 부분이라던가를 알려면
이 버텍스 버퍼 자체를 한 개를 만들어서 한번에 다 그리는 게 아니라
버텍스 버퍼 자체를 여러개를 만들어서 아하... 버텍스 버퍼를 여러개 만들어서 버텍스 버퍼가 더이상 필요 없어지면 다른 용도로 쓰거나 free하고
뭐 그러면 되겠구만.

파거나 하는 부분만 항상 새롭게 계산해 주면 된다!
레벨 6 수준이면 몇개가 되지...
레벨 5수준이면 몇개?
레벨 3 정도 수준으로 버텍스 버퍼를 여러개로 나누면 될 것 같다. 그럼 청크 하나에 64개의 버텍스 버퍼가 나온다. 이정도면 될 듯. 사이즈가 0인 건 그려지지도 않을테니....
그리고 변형되는 레벨3수준의 청크는 파면 버텍스를 추가하고 쌓아도 버텍스를 추가하고 버텍스를 없애는 건 뭐랄까 뭐 30초에 한번씩 업뎃으로 하고 이러면 될 것 같다.
---------------------------------------------------
캐슁 완료. 이제 radiosity....는 나중에 하자;;
일단 OpenGL로 진행되는 라이팅을 죄다 컬러버퍼로 바꿔야함. 그 전에, 각 버텍스의 컬러를 다르게 설정하면 그냥.... 비슷함.
--------------------------
음 그냥 주변 vertex color를 읽어와서 그거랑 선형보정? -_-?
좀 느리긴 할지도 모르겠지만 어차피 한번 그리는거고, 태양이면 고정이니까....
그거까지만 해도 굉장히 멋질것 같고, OpenGL라이팅을 끄면 radiosity만한 효과가 나올 것도 같고.
이런건 나중에 하고 이제 전투아이템을 만들어보고 아이템과 몹의 인터랙션을 간단하게 구현해보자. 스탯과 아이템을 구현해야!
-------
Entity에 OnDead이벤트 등이나 OnHit등을 바인드하게 해줘서 죽거나 맞을 때 애니메이션이나 제거, 아이템스폰 등을 처리해줘야 한다.
----
음 예제 게임을 만들면 게임 만들기가 아주 쉽게 해서 게임 만드는 툴 자체를 만들어보자.
-----
약한 아이템을 만들면 재미없으니까 일단 먼치킨 아이템과 먼치킨 몹으로 시작하자. 시작캐릭터도 먼치킨 그럼 누가이기지
키우는 재미 없이 플레이하고 아이템 얻는 재미만 얻도록 하자.
아...음..... 아이템을 사용할 수는 있지만 경제적인 요소에 더 집중을 일단

그러면..... 대화창을 만들고 선택할 수 있는 메뉴ㅜ가 있어야겠지.
파일 선택창을 개조하면 될 듯.
상점창도 있어야 하겠고..뭐.

캐슁을 했더니 넓은시야에서는 더 빠르고 좁은 시야에서는 좀 더 느린 것 같다. 시야가 좁으면 프러스텀컬링을 하는데 그게 잘 안되나?
---------------------------------------------
일단 캐릭터를 만들자....
스탯창, 스킬창을 만들자.
---------
스탯이나 스킬을 마음대로 올리면서 커스터마이징 해서 키우는 거 말고
그냥 드래곤퀘스트처럼 fixed된 걸 만들고
디아2에서 자주쓰이는 캐릭터 템플릿이나 울온의 템플릿처럼 좋은 템플릿을 만든다.
간단하게.
---------
일단 스킬을 사용할 수 있어야 한다.
스킬은 퀵바에 넣을 수 있다.
퀵바를 여러개 두고 퀵바 셀렉터에서 선택하도록 한다. 건설용, 마법용 등등으로 쓰도록.
Q를 누르고 1~0을 누르면 퀵바가 바뀐다.
좌/우측버튼 스킬설정
퀵바 스킬설정
아. 전투모드, 건설모드 따로 두고 퀵바 선택도 따로 하게하고 뭐 그럼 되나?
퀵바를 여러개를 두나.....
---------------------
음 무기 스탯은 드래곤퀘스트 비슷한 시스템을 넣어보자.
클래스를 고르는 것도 아니고 아예 드퀘4처럼 캐릭터를 고정해 보자.
주인공 역시 고정되어있음
-------
음.................게임 자체에 내가 질려있어서 그다지 재밌지가 못하다. 으헝헝
애니는...나중에 하고 공격하는 표시를 어떤게 할가?
----------------
공격표시는 크로스헤어의 배경을 색을 바꿔서 했다.
이제 음.... 아 알았다. 무기라던가 이런것의 실체에 대한 이미지가 머릿속에 너무 강해서, 무기 자체나 전투 자체의 실체는 보잘것없는 숫자라는 것을
잠시 잊고 있었다는. 게임 자체에서 보여주는 건 별로 없다. 상상력이 중요한 것. 게임을 하기가 힘든 건 상상을 하기가 힘들기 때문에 더욱 그렇지 않을까.
하여간에... 적은 정보와 알맞는 연출로 상상하기가 쉽도록 만들어주는 게 중요한 듯.
----------
스포너나 코드는 오른쪽 메뉴에서 파괴 버튼을 눌러야 파괴되도록 한다.
--------------
기본 게임 틀을 만들고, 유져가 게임 자체를 제작해서 다른사람이 플레이할 수 있게 유저 스스로 퀘스트나 아이템 등을 만들 수 있도록 한다.
admin모드로 들어가면 누구나 수정 가능하고 뭐 그런식.
멀티플레이어 가능하게 하면 진짜 좋을 거 같긴 하다.
------
self.mobs가 출현하는게 8군데 있다.(AppSt.mobs 이걸 그냥 그..... 딕셔너리 기반으로 해서 그.....
현재 청크 주변에 있는 딕셔너리에 있는 몹들만 표시되도록. 몹이 이동할 때마다 아...그 네트워크 게임에서도 비슷하게 했었지.
-----
이제 미니맵과 북쪽표시하기.
원형으로 해서 회전도 시켜야함
가장 높은 y청크를 얻어서 이미지로 C에서 만든 다음에 파이썬스트링으로 만들어서 파이썬으로 전달하면 여기서 텍스쳐 생성/리젠할때쓰면 됨
---------
왜 전투하는걸 못만드는지 알았다. RPG게임에서 전투는 가장 하기 싫은 "일"이다. 일거리를 만들려니 하기가 힘든 것.
-------
        # 스포너 뿐만이 아니라, 덮어씌울때 모든 아이템이나 상자등을 다 어떻게 처리한다? 아예, 그곳에 상자나 아이템이 있으면 로드하지 못하게
        # 막아야 할 것 같다. XXX:
        # 또한 복사할 때 스포너나 아이템이 복사되지 않도록 해야한다.(상자, 스포너, 코드블락)?
        # 음......여러가지 장치를 해둔 경우 그것도 복사하고 싶겠지만 그건 걍 포기??
        # 그것도 다 복사되게 해야하는 듯. 특히 복사하는 용도의 스포너는 복사하지 않고, 그 외의 스포너는 복사를 하되
        # 만약 스포너의 이름이 중복되는 경....음.................
        #
        # 아예 어드민의 용도로만 사용하게 하도록 하자 그냥;;
        # XXX: 이제 부수지 못하도록 스포너 2개로 Lockdown거는 것을 구현하자. 락다운을 걸면 땅의 주인만 락다운을 풀 수가 있음
        # 땅의 소유지를 결정하는 것도 스포너 2개로.
------------------------------
게임을 만드는 게임. 게임을 만드는 것 자체가 재미있으니까 게임을 만드는 게임. (....)
------------------------------
이제 계단을 만들어 보자.
그냥 Move함수에서 그리고 FallOrJump함수에서 조금씩 올라가거나 조금씩 내려가도록 boundy+위치y를 기반으로 검사해서 올려주거나 내려주면 된다.
----------
결국엔 몹이라던가 이런거 전부 C로 옮겨야 하겠지만 일단 여기서 계단을 만들어 보자.
-----------
GUI를 안그리면 30FPS가 나온다. 즉, 전부 C로 옮기고 vertexpointer를 쓰면 빠르지 않을까 싶다.
vertexpointer를 64번에 나눠 쓰는 것보다 한번에 쓰는것 역시 더 빨라지지 않을까? 메모리 복사가 가끔 일어나겠지만 말이다.

메모리 복사가 안일어나려면 그냥 음....여러번에 그리는 게 더 나을까?
------------
GUI를 일단 리스트에 버텍스, texit, texcoord, color, line인지 quad인지 여부를 다 저장해두고
업데이트가 한개라도 되었으면 rebuildvertexpointer로 전달해서 새로 만들고
업뎃이 안된 경우 그냥 전달해서 그린다.
아마 픽셀을 그리는 게 느린 경우일 수도 있다고 생각하지만 맵을 그리는 것도 빠른데 설마 그게 느려서 그런 건 아닌 것 같고
glbegin이 심각하게 느린걸로 생각된다. 그게 안느리다면 displaylist도 필요 없겠지.

아 그럼 gui를 디스플레이 리스트로 그리고 드래깅 중인 아이템만 그냥 그리고
나머지는 업뎃 될 때마다 디스플레이 리스트로 하고
게다가 뭐랄까 몹 애니메이션은...... 버텍스 애니메이션을 할까 스켈레탈 애니메이션 말고??
버텍스 숫자도 별로 안되는데 스켈레탈을 할 필요가 없는 듯?

버텍스 애니메이션은 매트릭스 트랜스폼이 없어서 더 빠른가? 한번 일단 테스트를

확실히 translation이 없으니까 훨씬... 빠르다.
하긴 translation이 있어도 빠르면 버텍스 애니메이션을 쓸 필요가 없었겠지
glGetMatrix?그걸로 로테이션 매트릭스를 가져와서 직접 변경시키고
각 프레임을 디스플레이 리스트로 만들어서 쓴다.
push하고 loadidentity부르고 로컬 회전/트랜슬레이션을 마친 후에 modelviewmatrix를 가져오면 될 듯 하다.
그리고 글로벌 트랜슬레이션/회전 한 번으로 한개의 몹을 그린다.
-----------------------
음 이제 큐브 인 프러스텀으로 했더니 G_FAR를 줄이면 좀 빨라진다.
-----------
태양광 계산도 버텍스 수준에서 하면 더 부드럽다.
그럼 그걸 하고 모든 라이팅을 버텍스라이팅으로 color버퍼로 하도록 해보자.
GenVerts에다가 태양의 Dir을 전해주면 그걸 GenQuads에서 써서한다
태양의 Y값이 0보다 크면 태양이 0인 것으로 간주한다.
하늘은....MODULATE로 어둡게 만들거나 점점 빨간색으로 바꾸다가 알파값을 0으로 만들기? 스카이박스를 안쓰고 밤이 있게하자.
계단도 태양광을 받아야 하고 몹도 태양광을 받아야 한다.
-----------------
자 저건 나중에 하고......이제 게임을 만들어 보자.
게임을 만든다는건
NPC인터랙션 메뉴를 만들고 상점등을 만들고
캐릭터 창을 만들고 스킬같은걸 고르게 하고
스킬을 사용하고 전투를 구현하고 뭐 그런걸 한다. 코드로 치면 게임의 내용과는 관계가 좀 없음

일단 장비를 입자

아이템 제작에 포지와 콜이나 챠콜이 필요하도록 하는 것도 필요하지만서도..
---------------
이제 인챈팅 테이블을 만들어서 아이템 인챈팅을 거기서 하도록 한다?
아니면... 인챈트 메뉴를 E버튼에 넣어 만들까.
음..........골드, 실버, 다이아몬드 한개와 인챈트 스크롤을 합치면 여러가지 속성이 있는 인챈트 스크롤이 나온다?
가장 약한 아이템이라도 실버/골드/다이아중 하나가 든다. 실버 골드 다이아는 희소성이 비슷하기 때문에 그냥....
속성이 다른 인챈트 스크롤이 나오기로 하고, 플레이어의 어떤 특정한 속성에 비례해서 더 좋은 인챈트 스크롤이 나오도록 하자.
아이템은 최대 5회 인챈트를 할 수 있고, 인챈트를 성공하면 스크롤의 속성이 ADD되며, 인챈트를 실패하면 스크롤이 날아간다는 슬픈 이야기가.
--------------------------------
"""
