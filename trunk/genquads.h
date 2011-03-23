/*
DigDigRPG
Copyright (C) 2011 Jin Ju Yu

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
#ifndef __GEN_QUADS_H__
#define __GEN_QUADS_H__ 1
typedef struct tXYZ {
    float x,y,z;
} XYZ;
typedef struct tXY {
    float x,y;
} vec2;
typedef struct tChunk {
    unsigned char *chunk;
    unsigned char *colors;
    char *heights;
    int x,y,z;
} Chunk;
typedef struct tOctree {
    struct tOctree *parent;
    struct tOctree **children;
    int filled;
    void *extra;
} Octree;
typedef struct tTorch {
    int x,y,z,face;
} Torch;
typedef struct tChest {
    int x,y,z,frontFacing;
} Chest;
typedef struct tItem {
    int type;
    float x;
    float y;
    float z;
    int idx;//파이썬에서 아이템이나 몹의 속성을 읽어옴
} Item;
typedef struct tExtra {
    Torch *torches;
    int torchLen;
    int torchIdx;
    Chest *chests;
    int chestLen;
    int chestIdx;
    Item *items;
    int itemLen;
    int itemIdx;
} Extra;


enum OctreeFilledFlag {
    OT_FILLED = 1 << 0,
    OT_HALFFILLED = 1 << 1,
    OT_EMPTY = 1 << 2,
    OT_COMPLETETRANSPARENT = 1 << 3,
    OT_PARTTRANSPARENT = 1 << 4,
    OT_XBLOCK = 1 << 5,
    OT_YBLOCK = 1 << 6,
    OT_ZBLOCK = 1 << 7,
};

typedef struct tQuaternion {
    float x,y,z,w;
} Quaternion;

enum BlockFlags
{
    // 여기에 추가할 때 중간에 껴넣게 되면 맵 다 깨짐!
     //총 256가지의 블럭종류들만이 가능하다.
     //블럭에 컬러를 넣고 싶다면 또다른 확장 데이터가 필요함.
     //뭐 컬러 버퍼라던지 그런 chunk.chunk를 또 만들면 된다.
    BLOCK_EMPTY,
    BLOCK_WATER,
    BLOCK_GLASS,
    BLOCK_LAVA,
    BLOCK_COBBLESTONE,
    BLOCK_LOG,
    BLOCK_WALL,
    BLOCK_BRICK,
    BLOCK_TNT,
    BLOCK_STONE,

    BLOCK_SAND, // 10
    BLOCK_GRAVEL,
    BLOCK_WOOD,
    BLOCK_LEAVES,
    BLOCK_SILVER,
    BLOCK_GOLD,
    BLOCK_COALORE,
    BLOCK_IRONORE,
    BLOCK_DIAMONDORE,
    BLOCK_IRON,
    
    BLOCK_DIAMOND, // 10
    BLOCK_CPU,
    BLOCK_CODE,
    BLOCK_ENERGY,
    BLOCK_KEYBIND,
    BLOCK_PANELSWITCH,
    BLOCK_LEVER,
    BLOCK_WALLSWITCH,
    BLOCK_NUMPAD,
    BLOCK_TELEPORT,

    BLOCK_JUMPER, // 10
    BLOCK_ELEVATOR,
    BLOCK_ENGINECORE,
    BLOCK_CONSTRUCTIONSITE,
    BLOCK_AREASELECTOR,
    BLOCK_GOLDORE,
    BLOCK_SILVERORE,
    BLOCK_WOOL,
    BLOCK_GRASS,
    BLOCK_DIRT,
    BLOCK_INDESTRUCTABLE,
    BLOCK_CHEST,
    BLOCK_SPAWNER,
    BLOCK_SILVERSLOT,
    BLOCK_GOLDSLOT,
    BLOCK_DIAMONDSLOT,
    // 음 if else도 좋지만 뭐랄까.. synthmaker처럼 한다.
};


char HitBoundingBox(float minB[3],float maxB[3], float origin[3], float dir[3],float coord[3]);

int InWater(float x, float y, float z, float vx, float vy, float vz);
int CheckCollide(float x, float y, float z, float vx, float vy, float vz, float bx, float by, float bz, float ydiff);
void FixPos(float *fx, float *fy,float *fz, float ox,float oy,float oz,float nx,float ny,float nz,int bx,int by,int bz, Octree *octrees[9], Chunk *chunks[9], int pos[9][3]);
void FillHeights(Chunk *chunk);
int PickWithMouse(XYZ vp, XYZ dirV, int pos[9][3], Octree *octrees[9], Chunk *chunks[9], int outCoords[3], int *outFace, int limit, float ydiff, float viewmat[16]);
void FillMap(unsigned char *chunkData);
void FillTerrain(unsigned char *chunkData, int *points, int len, int ox, int oy, int oz, int upward, int lwidth, int rwidth, int bwidth, int twidth, int heightlimit, unsigned char fill1, unsigned char fill2, unsigned char fill3);
void FillSea(unsigned char *chunkData, int *points, int len, int ox, int oy, int oz, int upward, int lwidth, int rwidth, int bwidth, int twidth, int heightlimit, unsigned char fill1, unsigned char fill2, unsigned char fill3, int depth);
void CalcRecursive(Chunk * chunk, Octree *octree, int x, int y, int z, int depth);
int IsPolyFront(int place, int x, int y, int z, float vx, float vy, float vz);
void GenQuad(float *quadBuffer, int place, int x, int y, int z);
Octree *AccessRecur(Octree *parent, int curx, int cury, int curz, int targetx, int targety, int targetz, int depth, int targetdepth);
Octree *AccessOctreeWithXYZ(Octree * root, int x, int y, int z, int targetdepth);
int CubeInFrustum(float x, float y, float z, double size, double frustum[6][4]);
void GenQuads(float *tV[64], float *tT[64], unsigned char *tC[64], int tIdx[64], int tLen[64], float *nsV[64], float *nsT[64], unsigned char *nsC[64], int nsIdx[64], int nsLen[64], float *aV[64], float *aT[64], unsigned char *aC[64], int aIdx[64], int aLen[64], float *iV[64], float *iT[64], unsigned char *iC[64], int iIdx[64], int iLen[64], Octree *root, Octree *parent, Chunk *chunk, Octree **octrees, Chunk **chunks, int pos[9][3], int depth, double frustum[6][4], int x, int y, int z, int ox, int oy, int oz, float vx, float vy, float vz, int lx, int ly, int lz, int updateCoords[64*3], int drawIdx, float sunx, float suny, float sunz);
void FillTrees(Chunk *chunk, char trees[1000]);
void GenIndexList(unsigned int *outIndexList, int *outIndexLen, float *quads, int quadLen, float vx, float vy, float vz);
#endif
