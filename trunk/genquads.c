#include "genquads.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifndef true
#define true 1
#endif

#ifndef false
#define false 0
#endif



#define LIGHTMAP_SIZE 16
typedef struct tsurface {
	float vertices[4][3];
	float matrix[9];
	float s_dist, t_dist;
} Surface;

float
dot_product(float v1[3], float v2[3])
{
	return (v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]);
}

void
normalize(float v[3])
{
	float f = 1.0f / sqrt(dot_product(v, v));

	v[0] *= f;
	v[1] *= f;
	v[2] *= f;
}

void
cross_product(const float *v1, const float *v2, float *out)
{
	out[0] = v1[1] * v2[2] - v1[2] * v2[1];
	out[1] = v1[2] * v2[0] - v1[0] * v2[2];
	out[2] = v1[0] * v2[1] - v1[1] * v2[0];
}

void
multiply_vector_by_matrix(const float m[9], float v[3])
{
	float tmp[3];

	tmp[0] = v[0] * m[0] + v[1] * m[3] + v[2] * m[6];
	tmp[1] = v[0] * m[1] + v[1] * m[4] + v[2] * m[7];
	tmp[2] = v[0] * m[2] + v[1] * m[5] + v[2] * m[8];

	v[0] = tmp[0];
	v[1] = tmp[1];
	v[2] = tmp[2];
}

Surface *
new_surface(float vertices[4][3])
{
	int i, j;
	Surface *surf;

	surf = malloc(sizeof(Surface));
	if(!surf) {
		fprintf(stderr, "Error: Couldn't allocate memory for surface\n");
		return NULL;
	}

	for(i = 0; i < 4; i++) {
		for(j = 0; j < 3; j++)
			surf->vertices[i][j] = vertices[i][j];
	}

	/* x axis of matrix points in world space direction of the s texture axis */
	for(i = 0; i < 3; i++)
		surf->matrix[0 + i] = surf->vertices[3][i] - surf->vertices[0][i];
	surf->s_dist = sqrt(dot_product(surf->matrix, surf->matrix));
	normalize(surf->matrix);

	/* y axis of matrix points in world space direction of the t texture axis */
	for(i = 0; i < 3; i++)
		surf->matrix[3 + i] = surf->vertices[1][i] - surf->vertices[0][i];
	surf->t_dist = sqrt(dot_product(surf->matrix + 3, surf->matrix + 3));
	normalize(surf->matrix + 3);

	/* z axis of matrix is the surface's normal */
	cross_product(surf->matrix, surf->matrix + 3, surf->matrix + 6);

	return surf;
}

void GetLocalCoords(int *a, int *b, int *c, int *A, int *B, int *C, int x, int y, int z)
{
    (*a) = x;
    (*b) = y;
    (*c) = z;
    while((*a) < 0)
        (*a) += 128;
    (*a) %= 128;

    while((*c) < 0)
        (*c) += 128;
    (*c) %= 128;
    if(*b < 0)
        *b = 0;
    if(*b >= 128)
        *b = 127;

    (*A) = x - (*a);
    (*B) = 0;
    (*C) = z - (*c);

}
/*
 ****
 ****
 ****
 ****
 */
void GetChunkByCoord(Chunk **chunk, Chunk *chunks[9], int pos[9][3], int a, int b, int c, int A, int B, int C)
{
    *chunk = NULL;
    int ii,jj;
    for(ii=0;ii<9;++ii)
    {
        if(pos[ii][0] == A && pos[ii][2] == C)
        {
            *chunk = chunks[ii];
            return;
        }
    }
}

/*
 * 음.. 일단 텍스쳐를 준비하고, 라잇맵은 무조건 16x16으로 하기로 하고
 * (512/5126)^2만큼의 폴리곤에 텍스쳐 1개를 생성하도록 한다.
 * 한장에 쿼드 1024개를 담을 수 있으니까
 * 보통 평균 렌더링 4000개를 하게 되니 대충 4장이면 쇼부 본다.
 *
 * 매번 라잇맵을 생성해도 빠르면 그냥 쓰고
 * 느리면 이걸 캐슁을 해서 블럭을 저장하듯 라잇맵을 옥트리에 저장해 버린다.
 * 16x16이 현재 빛이 닿는 즉 6면검사에서 보일 가능성이 있는 면들만 본다면
 * 청크당 평균 128x128개이다.(16384)
 * 또한 빛이 어떤 블럭들에 의해 가려지거나 이러면 진짜 어두워진다. 햇빛은 따로 있고 Torch도 따로 있고 이렇게 해야할텐데.
 * Radiosity가 필요한가?
 *
 */
/*
static float light_pos[3] = { 1.0f, 0.0f, 0.25f };
static float light_color[3] = { 1.0f, 1.0f, 1.0f };

static unsigned int
generate_lightmap(Surface *surf)
{
	static unsigned char data[LIGHTMAP_SIZE * LIGHTMAP_SIZE * 3];
	static unsigned int lightmap_tex_num = 0;
	unsigned int i, j;
	float pos[3];
	float step, s, t;

	if(lightmap_tex_num == 0)
		glGenTextures(1, &lightmap_tex_num);

	step = 1.0f / (float)LIGHTMAP_SIZE;

	s = t = 0.0f;
	for(i = 0; i < LIGHTMAP_SIZE; i++) {
		for(j = 0; j < LIGHTMAP_SIZE; j++) {
			float d;
			float tmp;

			pos[0] = surf->s_dist * s;
			pos[1] = surf->t_dist * t;
			pos[2] = 0.0f;
			multiply_vector_by_matrix(surf->matrix, pos);

			pos[0] += surf->vertices[0][0];
			pos[1] += surf->vertices[0][1];
			pos[2] += surf->vertices[0][2];

			pos[0] -= light_pos[0];
			pos[1] -= light_pos[1];
			pos[2] -= light_pos[2];

			d = dot_product(pos, pos) * 0.5f;
			if(d < 1.0f)
				d = 1.0f;
			tmp = 1.0f / d;

			data[i * LIGHTMAP_SIZE * 3 + j * 3 + 0] = (unsigned char)(255.0f * tmp * light_color[0]);
			data[i * LIGHTMAP_SIZE * 3 + j * 3 + 1] = (unsigned char)(255.0f * tmp * light_color[1]);
			data[i * LIGHTMAP_SIZE * 3 + j * 3 + 2] = (unsigned char)(255.0f * tmp * light_color[2]);

			s += step;
		}

		t += step;
		s = 0.0f;
	}

	glBindTexture(GL_TEXTURE_2D, lightmap_tex_num);
	glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
	glTexImage2D(GL_TEXTURE_2D, 0, 3, LIGHTMAP_SIZE, LIGHTMAP_SIZE, 0, GL_RGB, GL_UNSIGNED_BYTE, data);

	return lightmap_tex_num;
}

static int lighting = 1;

void
scene_toggle_lighting()
{
	lighting = lighting ? 0 : 1;
}

static float cam_rot[3] = { 0.0f, 0.0f, 0.0f };

void
scene_render()
{
	static Surface *surfaces[6] = {NULL,NULL,NULL,NULL,NULL,NULL};
	static unsigned int surface_tex_num;
	int i;

	if(!surfaces[0]) {
		unsigned char *data;
		unsigned int width, height;
		float v[4][3];

		glEnable(GL_TEXTURE_2D);

		// * load texture * /
		data = read_pcx("texture.pcx", &width, &height);
		glEnable(GL_TEXTURE_2D);
		glGenTextures(1, &surface_tex_num);
		glBindTexture(GL_TEXTURE_2D, surface_tex_num);
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
		glTexImage2D(GL_TEXTURE_2D, 0, 3, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data);

		/* create surfaces * /
		v[0][0] = -1.0f; v[0][1] = 1.0f; v[0][2] = 3.0f;
		v[1][0] = -1.0f; v[1][1] = 1.0f; v[1][2] = 1.0f;
		v[2][0] = 1.0f; v[2][1] = 1.0f; v[2][2] = 1.0f;
		v[3][0] = 1.0f; v[3][1] = 1.0f; v[3][2] = 3.0f;
		surfaces[0] = new_surface(v);

		v[0][0] = 1.0f; v[0][1] = 1.0f; v[0][2] = -1.0f;
		v[1][0] = 1.0f; v[1][1] = -1.0f; v[1][2] = -1.0f;
		v[2][0] = -1.0f; v[2][1] = -1.0f; v[2][2] = -1.0f;
		v[3][0] = -1.0f; v[3][1] = 1.0f; v[3][2] = -1.0f;
		surfaces[1] = new_surface(v);

		v[0][0] = -1.0f; v[0][1] = 1.0f; v[0][2] = 1.0f;
		v[1][0] = -1.0f; v[1][1] = 1.0f; v[1][2] = -1.0f;
		v[2][0] = 1.0f; v[2][1] = 1.0f; v[2][2] = -1.0f;
		v[3][0] = 1.0f; v[3][1] = 1.0f; v[3][2] = 1.0f;
		surfaces[2] = new_surface(v);

		v[0][0] = 1.0f; v[0][1] = -1.0f; v[0][2] = 1.0f;
		v[1][0] = 1.0f; v[1][1] = -1.0f; v[1][2] = -1.0f;
		v[2][0] = -1.0f; v[2][1] = -1.0f; v[2][2] = -1.0f;
		v[3][0] = -1.0f; v[3][1] = -1.0f; v[3][2] = 1.0f;
		surfaces[3] = new_surface(v);

		v[0][0] = -1.0f; v[0][1] = 1.0f; v[0][2] = 1.0f;
		v[1][0] = -1.0f; v[1][1] = 1.0f; v[1][2] = -1.0f;
		v[2][0] = -1.0f; v[2][1] = -1.0f; v[2][2] = -1.0f;
		v[3][0] = -1.0f; v[3][1] = -1.0f; v[3][2] = 1.0f;
		surfaces[4] = new_surface(v);

		v[0][0] = 1.0f; v[0][1] = -1.0f; v[0][2] = 1.0f;
		v[1][0] = 1.0f; v[1][1] = -1.0f; v[1][2] = -1.0f;
		v[2][0] = 1.0f; v[2][1] = 1.0f; v[2][2] = -1.0f;
		v[3][0] = 1.0f; v[3][1] = 1.0f; v[3][2] = 1.0f;
		surfaces[5] = new_surface(v);
	}

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glLoadIdentity();
	glTranslatef(0.0f, 0.0f, -5.0f);
	glRotatef(cam_rot[0], 1.0f, 0.0f, 0.0f);
	glRotatef(cam_rot[1], 0.0f, 1.0f, 0.0f);
	glRotatef(cam_rot[2], 0.0f, 0.0f, 1.0f);

	glActiveTextureARB(GL_TEXTURE0_ARB);
	glEnable(GL_TEXTURE_2D);
	glBindTexture(GL_TEXTURE_2D, surface_tex_num);
	glActiveTextureARB(GL_TEXTURE1_ARB);
	if(lighting)
		glEnable(GL_TEXTURE_2D);

	for(i = 0; i < 6; i++) {
		if(!surfaces[i])
			break;

		if(lighting)
			glBindTexture(GL_TEXTURE_2D, generate_lightmap(surfaces[i]));
		glBegin(GL_QUADS);
			glMultiTexCoord2fARB(GL_TEXTURE0_ARB, 0.0f, 0.0f);
			glMultiTexCoord2fARB(GL_TEXTURE1_ARB, 0.0f, 0.0f);
			glVertex3fv(surfaces[i]->vertices[0]);
			glMultiTexCoord2fARB(GL_TEXTURE0_ARB, 0.0f, 1.0f);
			glMultiTexCoord2fARB(GL_TEXTURE1_ARB, 0.0f, 1.0f);
			glVertex3fv(surfaces[i]->vertices[1]);
			glMultiTexCoord2fARB(GL_TEXTURE0_ARB, 1.0f, 1.0f);
			glMultiTexCoord2fARB(GL_TEXTURE1_ARB, 1.0f, 1.0f);
			glVertex3fv(surfaces[i]->vertices[2]);
			glMultiTexCoord2fARB(GL_TEXTURE0_ARB, 1.0f, 0.0f);
			glMultiTexCoord2fARB(GL_TEXTURE1_ARB, 1.0f, 0.0f);
			glVertex3fv(surfaces[i]->vertices[3]);
		glEnd();
	}

	/// * render light * /
	glDisable(GL_TEXTURE_2D);
	glActiveTextureARB(GL_TEXTURE0_ARB);
	glDisable(GL_TEXTURE_2D);
	glColor3fv(light_color);
	glBegin(GL_QUADS);
		glVertex3f(light_pos[0] - 0.05f, light_pos[1] + 0.05f, light_pos[2] + 0.05f);
		glVertex3f(light_pos[0] - 0.05f, light_pos[1] - 0.05f, light_pos[2] + 0.05f);
		glVertex3f(light_pos[0] + 0.05f, light_pos[1] - 0.05f, light_pos[2] + 0.05f);
		glVertex3f(light_pos[0] + 0.05f, light_pos[1] + 0.05f, light_pos[2] + 0.05f);
	glEnd();
	glColor4f(1.0f, 1.0f, 1.0f, 1.0f);

	glFlush();
	glutSwapBuffers();
}

static unsigned int
get_ticks()
{
	struct timeval t;

	gettimeofday(&t, NULL);

	return (t.tv_sec * 1000) + (t.tv_usec / 1000);
}

void
scene_cycle()
{
	static float light_rot = 0.0f;
	static unsigned int prev_ticks = 0;
	unsigned int ticks;
	float time;

	if(!prev_ticks)
		prev_ticks = get_ticks();

	ticks = get_ticks();
	time = (float)(ticks - prev_ticks);
	prev_ticks = ticks;

	cam_rot[2] -= 0.06 * time;
	while(cam_rot[2] < 0.0f)
		cam_rot[2] += 360.0f;

	light_pos[0] = cos(light_rot) * 0.8f;
	light_pos[1] = sin(light_rot) * 0.8f;
	light_rot += 0.001f * time;

	scene_render();

*/



/*
   Determine whether or not the line segment p1,p2
   Intersects the 3 vertex facet bounded by pa,pb,pc
   Return true/false and the intersection point p

   The equation of the line is p = p1 + mu (p2 - p1)
   The equation of the plane is a x + b y + c z + d = 0
                                n.x x + n.y y + n.z z + d = 0
*/
const float RTOD = 180.0/3.14159265;
const float EPS = 0.00001;
double ABS(double number)
{
    if(number < 0.0)
        return -number;
    return number;
}
float Length(XYZ *v)
{
    return sqrt(v->x*v->x+v->y*v->y+v->z*v->z);
}

void Cross(XYZ *out, XYZ *a, XYZ *b)
{
    out->x = a->y*b->z-a->z*b->y;
    out->y = a->z*b->x-a->x*b->z;
    out->z = a->x*b->y-a->y*b->x;
}
float Dot(XYZ *a, XYZ *b)
{
    return a->x*b->x+a->y*b->y+a->z*b->z;
}
void Normalize(XYZ *out, XYZ *v)
{
    float len;
    len = Length(v);
    if(len < 0.0001)
        len = 0.0001;
    out->x = v->x/len;
    out->y = v->y/len;
    out->z = v->z/len;
}

void MultScalar(XYZ *out, XYZ *v, float s)
{
    out->x = v->x * s;
    out->y = v->y * s;
    out->z = v->z * s;
}

void AddVector(XYZ *out, XYZ *a, XYZ *b)
{
    out->x = a->x + b->x;
    out->y =  a->y + b->y;
    out->z =  a->z + b->z;
}

void SubsVector(XYZ *out, XYZ *a, XYZ *b)
{
    out->x = a->x - b->x;
    out->y = a->y - b->y;
    out->z = a->z - b->z;
}

int RayQuadIntersect(p1,p2,pa,pb,pc,pd,p)
XYZ p1,p2,pa,pb,pc,pd,*p;
{
    //printf("QUAD: %f %f %f, %f %f %f, %f %f %f, %f %f %f\n", pa.x, pa.y, pa.z, pb.x, pb.y,pb.z,pc.x,pc.y,pc.z,pd.x,pd.y,pd.z);

    if(RayTryIntersect(p1,p2,pa,pb,pc,p))
        return true;
    if(RayTryIntersect(p1,p2,pc,pd,pa,p))
        return true;
    return false;
}
int RayTryIntersect(p1,p2,pa,pb,pc,p)
XYZ p1,p2,pa,pb,pc,*p;
{
   double d;
   double a1,a2,a3;
   double total,denom,mu;
   XYZ n,pa1,pa2,pa3;

   /* Calculate the parameters for the plane */
   n.x = (pb.y - pa.y)*(pc.z - pa.z) - (pb.z - pa.z)*(pc.y - pa.y);
   n.y = (pb.z - pa.z)*(pc.x - pa.x) - (pb.x - pa.x)*(pc.z - pa.z);
   n.z = (pb.x - pa.x)*(pc.y - pa.y) - (pb.y - pa.y)*(pc.x - pa.x);
   Normalize(&n, &n);
   d = - n.x * pa.x - n.y * pa.y - n.z * pa.z;

   /* Calculate the position on the line that intersects the plane */
   denom = n.x * (p2.x - p1.x) + n.y * (p2.y - p1.y) + n.z * (p2.z - p1.z);
   if (ABS(denom) < EPS)         /* Line and plane don't intersect */
      return false;
   mu = - (d + n.x * p1.x + n.y * p1.y + n.z * p1.z) / denom;
   p->x = p1.x + mu * (p2.x - p1.x);
   p->y = p1.y + mu * (p2.y - p1.y);
   p->z = p1.z + mu * (p2.z - p1.z);
   if (mu < 0.0f || mu > 1.0f)   /* Intersection not along line segment */
      return false;

   /* Determine whether or not the intersection point is bounded by pa,pb,pc */
   pa1.x = pa.x - p->x;
   pa1.y = pa.y - p->y;
   pa1.z = pa.z - p->z;
   Normalize(&pa1, &pa1);
   pa2.x = pb.x - p->x;
   pa2.y = pb.y - p->y;
   pa2.z = pb.z - p->z;
   Normalize(&pa2, &pa2);
   pa3.x = pc.x - p->x;
   pa3.y = pc.y - p->y;
   pa3.z = pc.z - p->z;
   Normalize(&pa3, &pa3);
   a1 = pa1.x*pa2.x + pa1.y*pa2.y + pa1.z*pa2.z;
   a2 = pa2.x*pa3.x + pa2.y*pa3.y + pa2.z*pa3.z;
   a3 = pa3.x*pa1.x + pa3.y*pa1.y + pa3.z*pa1.z;
   total = (acos(a1) + acos(a2) + acos(a3)) * RTOD;
   if (ABS(total - 360.0f) > EPS)
   {
      return false;
   }

   return true;
}

#define NUMDIM	3
#define RIGHT	0
#define LEFT	1
#define MIDDLE	2

char HitBoundingBox(minB,maxB, origin, dir,coord)
float minB[NUMDIM], maxB[NUMDIM];		/*box */
float origin[NUMDIM], dir[NUMDIM];		/*ray */
float coord[NUMDIM];				/* hit point */
{
	char inside = true;
	char quadrant[NUMDIM];
	register int i;
	int whichPlane;
	float maxT[NUMDIM];
	float candidatePlane[NUMDIM];

	/* Find candidate planes; this loop can be avoided if
   	rays cast all from the eye(assume perpsective view) */
	for (i=0; i<NUMDIM; i++)
		if(origin[i] < minB[i]) {
			quadrant[i] = LEFT;
			candidatePlane[i] = minB[i];
			inside = false;
		}else if (origin[i] > maxB[i]) {
			quadrant[i] = RIGHT;
			candidatePlane[i] = maxB[i];
			inside = false;
		}else	{
			quadrant[i] = MIDDLE;
		}

	/* Ray origin inside bounding box */
	if(inside)	{
		coord = origin;
		return (true);
	}


	/* Calculate T distances to candidate planes */
	for (i = 0; i < NUMDIM; i++)
		if (quadrant[i] != MIDDLE && dir[i] !=0.)
			maxT[i] = (candidatePlane[i]-origin[i]) / dir[i];
		else
			maxT[i] = -1.;

	/* Get largest of the maxT's for final choice of intersection */
	whichPlane = 0;
	for (i = 1; i < NUMDIM; i++)
		if (maxT[whichPlane] < maxT[i])
			whichPlane = i;

	/* Check final candidate actually inside box */
	if (maxT[whichPlane] < 0.) return (false);
	for (i = 0; i < NUMDIM; i++)
		if (whichPlane != i) {
			coord[i] = origin[i] + maxT[whichPlane] *dir[i];
			if (coord[i] < minB[i] || coord[i] > maxB[i])
				return (false);
		} else {
			coord[i] = candidatePlane[i];
		}
	return (true);				/* ray hits box */
}	



int PickWithMouse(XYZ vp, XYZ dirV, int pos[9][3], Octree *octrees[9], Chunk *chunks[9], int outCoords[3], int *outFace, int limit, float ydiff, float viewmat[16])
    // y값이 128을 벗어나거나 0보다 작을 때의 경우를 잘 해결해야 한다.
{
    // 여기서 "앞면"인 폴리곤만 pick할 수 있게 한다.
    // 걍.....서있는 자리에서 45도 각도로 잡고
    // 눈앞 9개 블럭 중 하나를 선택하게 한다? ㄴㄴ.... block/ray 알고리즘을 찾아야할지도 모르겠다.
    unsigned char blocks[9*9*9];
    int foundFaces[9*9*9];
    int lowestFace;
    XYZ foundIntersections[9*9*9];
    XYZ lowestIntersection;
    int foundCoords[9*9*9][3];
    int lowestCoord[3];
    int foundIdx = 0;
    int x,y,z;
    float spx,spy,spz;
    float cx,cy,cz;
    int i,j,k;
    int ii,jj,kk;
    int a,b,c,A,B,C;
    XYZ aa,bb,cc,dd;
    XYZ intersection;
    int intersects;
    x = (int)(vp.x-0.5f);
    y = (int)(vp.y-0.5f);
    z = (int)(vp.z-0.5f);
    x -= 4;
    y -= 4;
    z -= 4;
    Chunk *curChunk;
    for(k=0;k<9;++k)
    {
        for(j=0;j<9;++j)
        {
            for(i=0;i<9;++i)
            {
                // Get Local Coords
                GetLocalCoords(&a,&b,&c,&A,&B,&C,x+i,y+j,z+k);
                GetChunkByCoord(&curChunk, chunks, pos, a,b,c,A,B,C);
                if(curChunk && !(b < 0 || b >= 128))
                    blocks[k*9*9+j*9+i] = curChunk->chunk[c*128*128+b*128+a];
            }
        }
    }
    // 012 345 678
    // 01 23456 78
    // 0 1234567 8
    // 67890
    // 12345
    // 67890
    // 12345
    //ray sphere test를 한다.
    //가까운데 있는 블럭부터 해야하니까 주변 3x3x3블럭, 5x5x5블럭 등을 검사한다. 3블럭 이상 떨어졌는데 그걸 파겠다고? 안되지.
    // 아 근데...3블럭 이상 떨어졌어도 집 지을 땐 필요함.. 음....
    // blocks는 x,y,z가 가장 작은 값부터 가장 큰 값까지
    // 2,2,2가 오리진.
    // 
    // 아...주변 3x3x3블럭을 어떻게 검사한담? ^^;;;;
    // 아. 오리진에서부터 1 떨어진 놈들을 검사하면 된다.
    //found = []
    float makeCube[] = {-0.50f, -0.50f, -0.50f, 0.50f, -0.50f, -0.50f, 0.50f, -0.50f, 0.50f, -0.50f, -0.50f, 0.50f,
            -0.50f, 0.50f, -0.50f, 0.50f, 0.50f, -0.50f, 0.50f, 0.50f, 0.50f, -0.50f, 0.50f, 0.50f,
            -0.50f, 0.50f, -0.50f, -0.50f, 0.50f, 0.50f, -0.50f, -0.50f, 0.50f, -0.50f, -0.50f, -0.50f,
            0.50f, 0.50f, -0.50f, 0.50f, 0.50f, 0.50f, 0.50f, -0.50f, 0.50f, 0.50f, -0.50f, -0.50f,
            -0.50f, 0.50f, -0.50f, 0.50f, 0.50f, -0.50f, 0.50f, -0.50f, -0.50f, -0.50f, -0.50f, -0.50f,
            -0.50f, 0.50f, 0.50f, 0.50f, 0.50f, 0.50f, 0.50f, -0.50f, 0.50f, -0.50f, -0.50f, 0.50f};


    int radius, offset;
    int radiuses[] = {3,5,7,9};
    int offsets[] = {3,2,1,0};
    int l,m,n;
    int looped = 0, looped2=0;
    float w;
    XYZ oldVP;
    oldVP = vp;
    /*
    vp.x = vp.x*viewmat[0]+vp.x*viewmat[1]+vp.x*viewmat[2]+vp.x*viewmat[3];
    vp.y = vp.y*viewmat[4]+vp.y*viewmat[5]+vp.y*viewmat[6]+vp.y*viewmat[7];
    vp.z = vp.z*viewmat[8]+vp.z*viewmat[9]+vp.z*viewmat[10]+vp.z*viewmat[11];
    w = 1.0f*viewmat[12]+1.0f*viewmat[13]+1.0f*viewmat[14]+1.0f*viewmat[15];
    vp.x /= w;
    vp.y /= w;
    vp.z /= w;
    dirV.x = dirV.x*viewmat[0]+dirV.x*viewmat[1]+dirV.x*viewmat[2]+dirV.x*viewmat[3];
    dirV.y = dirV.y*viewmat[4]+dirV.y*viewmat[5]+dirV.y*viewmat[6]+dirV.y*viewmat[7];
    dirV.z = dirV.z*viewmat[8]+dirV.z*viewmat[9]+dirV.z*viewmat[10]+dirV.z*viewmat[11];
    w = 1.0f*viewmat[12]+1.0f*viewmat[13]+1.0f*viewmat[14]+1.0f*viewmat[15];
    dirV.x /= w;
    dirV.y /= w;
    dirV.z /= w;
    */

    for(kk=0;kk<4;++kk)
    {
        if(radiuses[kk] > limit)
        {
            break;
        }
        // 음 중복되는 부분은 피할 수 있다면 더 좋을텐데?
        // 음. 못찾으면 못찾을수록 더 돌아야 하는데 뭐 무슨 15,12번 돌고 만다. --; 뭔가 문제가 있음.
        for(k=0;k<radiuses[kk]-2;++k)
        {
            n = k + offsets[kk];
            if(k >= 1)
            {
                //if(k >= 1 && k <= radiuses[kk-1])
 //                   continue;
            }
            for(j=0;j<radiuses[kk]-0;++j)
            {
                m = j + offsets[kk];
                if(k >= 1)
                {
                    //if(j >= 1 && j <= radiuses[kk-1])
                     //   continue;
                }
                for(i=0;i<radiuses[kk];++i)
                {
                    if(k >= 1)
                    {
                        //if(i >= 1 && i <= radiuses[kk-1])
                         //   continue;
                    }
                    l = i + offsets[kk];
                    if(blocks[(n)*9*9+(m)*9+(l)] != 0) // 여기를 고치면 여러가지 블럭(물, 다른거) 등에 대해 다른 연산을 할 수 있다.
                    {
                        spx = x+l+0.5f;
                        spy = y+m+0.5f;
                        spz = z+n+0.5f;

                        float minB[3], maxB[3], origin[3], dir[3], coord[3];
                        // coord의 x,y,z값을 검사해서 spx,spx+1,spy,...spz+1값에 가장 가까운 것으로 6면검사를 한다.
                        minB[0] = spx-0.5f;
                        minB[1] = spy-0.5f;
                        minB[2] = spz-0.5f;
                        maxB[0] = spx+0.5f;
                        maxB[1] = spy+0.5f;
                        maxB[2] = spz+0.5f;
                        origin[0] = vp.x;
                        origin[1] = vp.y;
                        origin[2] = vp.z;
                        XYZ newDIR;
                        SubsVector(&newDIR, &dirV, &vp);
                        Normalize(&newDIR, &newDIR);
                        dir[0] = newDIR.x;
                        dir[1] = newDIR.y;
                        dir[2] = newDIR.z;
                        intersects = HitBoundingBox(minB,maxB, origin, dir,coord);
                        spx -= 0.5f;
                        spy -= 0.5f;
                        spz -= 0.5f;
                        int face = 1;
                        if(spy-EPS <= coord[1] && coord[1] <= spy+EPS)
                        {
                            face = 0;
                        }
                        else if(spy+1.0f-EPS <= coord[1] && coord[1] <= spy+1.0f+EPS)
                        {
                            face = 1;
                        }
                        else if(spx-EPS <= coord[0] && coord[0] <= spx+EPS)
                        {
                            face = 2;
                        }
                        else if(spx+1.0f-EPS <= coord[0] && coord[0] <= spx+1.0f+EPS)
                        {
                            face = 3;
                        }
                        else if(spz-EPS <= coord[2] && coord[2] <= spz+EPS)
                        {
                            face = 4;
                        }
                        else if(spz+1.0f-EPS <= coord[2] && coord[2] <= spz+1.0f+EPS)
                        {
                            face = 5;
                        }

                        if(intersects == true && IsPolyFront(face, x+l, y+m, z+n, oldVP.x, oldVP.y, oldVP.z))
                            //XXX: 여기에 물 파는 옵션이 있으면 물을 파고, 없으면 가장 가까운 땅을 파도록 바꿔야 한다.
                            //또한 물이 있어도 블럭을 쌓아 물을 막을 수 있도록 해야한다.
                            //XXX: 모래 땅으로 꺼지는 건 판쪽의 위의 연결된 모래를 다 찾아서 맨 위의 모래를 하나 없애고 판쪽에 모래를
                            //채우면 된다. 떨어지는 애니메이션만 만들어주면 됨 애니메이션 버퍼는 따로있음
                            //XXX: 팔 때마다 판 곳 주변에 물이 있는지 보고 물 흐르기를 구현한다.
                            //폭포와 같은 건 생성시에 이미 흐르는 폭포물줄기까지 다 생성하고
                            //물이 새로운 곳에 퍼졌을 경우
                            //땅을 팠을 경우에만 물 흐르기를 검사한다.
                            //한 번 흐른 물들은 계속해서 끝날 때 까지 흐르고
                            //다 흐르면 멈춘다. 흐르는 도중에 파인 땅 역시 검사함
                        {
                            intersection.x = coord[0];
                            intersection.y = coord[1];
                            intersection.z = coord[2];
                            foundFaces[foundIdx] = face;//ii;
                            foundIntersections[foundIdx] = intersection;
                            foundCoords[foundIdx][0] = x+l;
                            foundCoords[foundIdx][1] = y+m;
                            foundCoords[foundIdx][2] = z+n;
                            foundIdx++;
                        }
                    }
                }
            }
        }
        if(foundIdx != 0)
        {
            break;
        }

    }
    XYZ oldPoint;
    XYZ comp1, comp2;
    if(foundIdx != 0)
    {
        lowestFace = foundFaces[0];
        lowestIntersection = foundIntersections[0];
        lowestCoord[0] = foundCoords[0][0];
        lowestCoord[1] = foundCoords[0][1];
        lowestCoord[2] = foundCoords[0][2];
        // 아 이거를 해두고 나서 for문에서 못찾아버리면
        // 이거가 선택되겠지?
        // 이거가 만약 멀리있는거면 이거가 그대로 선택되겠지?
        
        for(i=1;i<foundIdx;++i)
        {
            oldPoint = lowestIntersection;
            SubsVector(&comp1, &oldPoint, &vp);
            SubsVector(&comp2, &foundIntersections[i], &vp);
            if(Length(&comp1) > Length(&comp2))
            {
                lowestFace = foundFaces[i];
                lowestIntersection = foundIntersections[i];
                lowestCoord[0] = foundCoords[i][0];
                lowestCoord[1] = foundCoords[i][1];
                lowestCoord[2] = foundCoords[i][2];
            }
        }
        outCoords[0] = lowestCoord[0];
        outCoords[1] = lowestCoord[1];
        outCoords[2] = lowestCoord[2];
        *outFace = lowestFace;
        return true;
    }
    else
    {
        return false;
    }
}

unsigned char GenOre(unsigned char y)
{
    unsigned char ores50[] = {
        BLOCK_COBBLESTONE,
        BLOCK_SAND,
        BLOCK_DIRT,
        BLOCK_IRONORE,
        BLOCK_COALORE
            };
    int num50 = 5;
    unsigned char ores40[] = {
        BLOCK_SILVERORE
            };
    int num40 = 1;
    unsigned char ores30[] = {
        BLOCK_GOLDORE
            };
    int num30 = 1;
    unsigned char ores20[] = {
        BLOCK_DIAMONDORE
            };
    int num20 = 1;
    int factor = 0;
    factor = rand()%100;
    if(y > 50)
    {
        if(factor > 35)
            return ores50[0];
        else if(factor > 30)
            return ores50[1];
        else if(factor > 25)
            return ores50[2];
        else if(factor > 20)
            return ores50[3];
        else
            return ores50[4];
    }
    else if(y > 40)
    {
        if(factor > 45)
            return ores50[0];
        else if(factor > 40)
            return ores50[1];
        else if(factor > 35)
            return ores50[2];
        else if(factor > 30)
            return ores50[3];
        else if(factor > 10)
            return ores50[4];
        else
            return ores40[0];
    }
    else if(y > 30)
    {
        if(factor > 55)
            return ores50[0];
        else if(factor > 50)
            return ores50[1];
        else if(factor > 45)
            return ores50[2];
        else if(factor > 40)
            return ores50[3];
        else if(factor > 20)
            return ores50[4];
        else if(factor > 10)
            return ores40[0];
        else
            return ores30[0];
    }
    else
    {
        if(factor > 65)
            return ores50[0];
        else if(factor > 60)
            return ores50[1];
        else if(factor > 55)
            return ores50[2];
        else if(factor > 50)
            return ores50[3];
        else if(factor > 30)
            return ores50[4];
        else if(factor > 20)
            return ores40[0];
        else if(factor > 10)
            return ores30[0];
        else
            return ores20[0];
    }



}

void FillSea(unsigned char *chunkData, int *points, int len, int ox, int oy, int oz, int upward, int lwidth, int rwidth, int bwidth, int twidth, int heightlimit, unsigned char fill1, unsigned char fill2, unsigned char fill3, int depth)
    // 아 이거 진짜 트릭키 한 것 같지만 그렇지 않다.
    // y값 위에 있는 블럭을 모두 제거하고 깔면 된다.
{
    int x,y,z, zSize=128*128,limit=128;
    int left, right, i,j;
    int height=0;
    int highestZ = 0;
    int lowestZ = 127;
    int highestX = 0;
    int lowestX = 127;
    int prevl = points[0], prevr = points[2];
    int dirtThick = 2;
    int grassThick = 3;
    int startY = 63;

    for(i=0;i<len/4;++i)
    {
        z = points[i*4+1];
        if(z > highestZ)
            highestZ = z;
        if(z < lowestZ)
            lowestZ = z;
    }

    for(i=0;i<len/4;++i)
    {
        left = points[i*4];
        right = points[i*4+2];
        if(right > highestX)
            highestX = right;
        if(left < lowestX)
            lowestX = left;
    }
    if(highestX < lowestX || highestZ < lowestZ)
    {
        printf("crap");
        return;
    }

    char *curpoints = (char*)malloc(sizeof(char)*(highestX-lowestX+1)*(highestZ-lowestZ+1));
    //char *xpoints = (char*)malloc(sizeof(char)*(highestX-lowestX+1)*2);
    memset(curpoints, 0, sizeof(char)*(highestX-lowestX+1)*(highestZ-lowestZ+1));
    prevl = points[0];
    prevr = points[2];
    int widthPerHeight = 3;
    for(i=0;i<len/4;++i)
    {
        z = points[i*4+1];
        left = points[i*4];
        right = points[i*4+2];
        if(right-left<4)
        {
            left = prevl;
            right = prevr;
        }
        prevl = left;
        prevr = right;
        for(x=left;x<=right;++x)
        {
            /*
            if(((z-lowestZ)*(highestX-lowestX+1)+x-lowestX) < 0)
                printf("cur error2\n");
            else if(((z-lowestZ)*(highestX-lowestX+1)+x-lowestX) >= (highestX-lowestX+1)*(highestZ-lowestZ+1))
                printf("cur error3\n");
                */
            curpoints[(z-lowestZ)*(highestX-lowestX+1)+x-lowestX] = 1;
        }
    }
    int count = 0;
    int zcount = 0;
    int zfound = false;
    for(height=0;height<heightlimit;++height)
    {
        if(height == 0 && upward == -1)
        {
            for(z=0;z<(highestZ-lowestZ+1);++z)
            {
                for(y=oy+1;y<oy+20;++y)
                {
                    for(x=0;x<(highestX-lowestX+1);++x)
                    {
                        if(curpoints[z*(highestX-lowestX+1)+x] == 1)
                            if(0 <= oz+z+lowestZ && oz+z+lowestZ < 128 && 0 <= ox+x+lowestX && ox+x+lowestX < 128 && 0 <= oy+height*upward && oy+height*upward < 128)
                            {
                                chunkData[(oz+z+lowestZ)*zSize+(y)*128+(ox+x+lowestX)] = BLOCK_EMPTY;
                            }
                    }
                }
            }
            for(z=0;z<(highestZ-lowestZ+1);++z)
            {
                for(y=oy-depth;y<oy;++y)
                {
                    for(x=0;x<(highestX-lowestX+1);++x)
                    {
                        if(curpoints[z*(highestX-lowestX+1)+x] == 1)
                            if(0 <= oz+z+lowestZ && oz+z+lowestZ < 128 && 0 <= ox+x+lowestX && ox+x+lowestX < 128 && 0 <= oy+height*upward && oy+height*upward < 128)
                            {
                                chunkData[(oz+z+lowestZ)*zSize+(y)*128+(ox+x+lowestX)] = fill2;
                            }
                    }
                }
            }
            for(z=0;z<(highestZ-lowestZ+1);++z)
            {
                for(x=0;x<(highestX-lowestX+1);++x)
                {
                    if(curpoints[z*(highestX-lowestX+1)+x] == 1)
                        if(0 <= oz+z+lowestZ && oz+z+lowestZ < 128 && 0 <= ox+x+lowestX && ox+x+lowestX < 128 && 0 <= oy+height*upward && oy+height*upward < 128)
                        {
                            chunkData[(oz+z+lowestZ)*zSize+(oy)*128+(ox+x+lowestX)] = BLOCK_EMPTY;
                        }
                }
            }
        }
        else
        {
            for(z=0;z<(highestZ-lowestZ+1);++z)
            {
                for(x=0;x<(highestX-lowestX+1);++x)
                {
                    if(curpoints[z*(highestX-lowestX+1)+x] == 1)
                        if(0 <= oz+z+lowestZ && oz+z+lowestZ < 128 && 0 <= ox+x+lowestX && ox+x+lowestX < 128 && 0 <= oy+height*upward && oy+height*upward < 128)
                        {
                            if(upward == 1)
                            {
                                chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward)*128+(ox+x+lowestX)] = fill1;
                                if(oy+height*upward-1 > 0)
                                    chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward-1)*128+(ox+x+lowestX)] = GenOre(oy+height*upward);
                            }
                            else if(upward == -1)
                            {
                                chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward)*128+(ox+x+lowestX)] = fill1;
                                if(oy+height*upward-1 > 0)
                                    chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward-1)*128+(ox+x+lowestX)] = fill3;
                            }
                        }
                }
            }
        }
        for(z=0;z<(highestZ-lowestZ+1);++z)
        { // 패턴깎기
            count = 0;
            for(x=0;x<(highestX-lowestX+1);++x)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1 && count < lwidth)
                {
                    curpoints[z*(highestX-lowestX+1)+x] = 0;
                    count++;
                }
                if(count == lwidth)
                    break;
            }
            count = 0;
            for(x=(highestX-lowestX+1)-1;x>=0;--x)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1 && count < rwidth)
                {
                    curpoints[z*(highestX-lowestX+1)+x] = 0;
                    count++;
                }
                if(count == rwidth)
                    break;
            }
        }

        for(x=0;x<(highestX-lowestX+1);++x)
        { // 패턴깎기
            count = 0;
            for(z=0;z<(highestZ-lowestZ+1);++z)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1 && count < bwidth)
                {
                    curpoints[z*(highestX-lowestX+1)+x] = 0;
                    count++;
                }
                if(count == bwidth)
                    break;
            }
            count = 0;
            for(z=(highestZ-lowestZ+1)-1;z>=0;--z)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1 && count < twidth)
                {
                    curpoints[z*(highestX-lowestX+1)+x] = 0;
                    count++;
                }
                if(count == twidth)
                    break;
            }
        }



    }
    free(curpoints);
}

void FillTerrain(unsigned char *chunkData, int *points, int len, int ox, int oy, int oz, int upward, int lwidth, int rwidth, int bwidth, int twidth, int heightlimit, unsigned char fill1, unsigned char fill2, unsigned char fill3)
{
    int x,y,z, zSize=128*128,limit=128;
    int left, right, i,j;
    int height=0;
    int highestZ = 0;
    int lowestZ = 127;
    int highestX = 0;
    int lowestX = 127;
    int prevl = points[0], prevr = points[2];
    int dirtThick = 2;
    int grassThick = 3;
    int startY = 63;

    for(i=0;i<len/4;++i)
    {
        z = points[i*4+1];
        if(z > highestZ)
            highestZ = z;
        if(z < lowestZ)
            lowestZ = z;
    }

    for(i=0;i<len/4;++i)
    {
        left = points[i*4];
        right = points[i*4+2];
        if(right > highestX)
            highestX = right;
        if(left < lowestX)
            lowestX = left;
    }
    if(highestX < lowestX || highestZ < lowestZ)
    {
        printf("crap");
        return;
    }

    char *curpoints = (char*)malloc(sizeof(char)*(highestX-lowestX+1)*(highestZ-lowestZ+1));
    //char *xpoints = (char*)malloc(sizeof(char)*(highestX-lowestX+1)*2);
    memset(curpoints, 0, sizeof(char)*(highestX-lowestX+1)*(highestZ-lowestZ+1));
    prevl = points[0];
    prevr = points[2];
    int widthPerHeight = 3;
    for(i=0;i<len/4;++i)
    {
        z = points[i*4+1];
        left = points[i*4];
        right = points[i*4+2];
        if(right-left<4)
        {
            left = prevl;
            right = prevr;
        }
        prevl = left;
        prevr = right;
        for(x=left;x<=right;++x)
        {
            /*
            if(((z-lowestZ)*(highestX-lowestX+1)+x-lowestX) < 0)
                printf("cur error2\n");
            else if(((z-lowestZ)*(highestX-lowestX+1)+x-lowestX) >= (highestX-lowestX+1)*(highestZ-lowestZ+1))
                printf("cur error3\n");
                */
            curpoints[(z-lowestZ)*(highestX-lowestX+1)+x-lowestX] = 1;
        }
    }
    int count = 0;
    int zcount = 0;
    int zfound = false;
    for(height=0;height<heightlimit;++height)
    {
        for(z=0;z<(highestZ-lowestZ+1);++z)
        {
            for(x=0;x<(highestX-lowestX+1);++x)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1)
                    if(0 <= oz+z+lowestZ && oz+z+lowestZ < 128 && 0 <= ox+x+lowestX && ox+x+lowestX < 128 && 0 <= oy+height*upward && oy+height*upward < 128)
                    {
                        if(upward == 1)
                        {
                            chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward)*128+(ox+x+lowestX)] = fill1;
                            if(oy+height*upward-1 > 0)
                                chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward-1)*128+(ox+x+lowestX)] = fill2;
                            if(oy+height*upward-2 > 0)
                                chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward-2)*128+(ox+x+lowestX)] = fill2;
                            if(oy+height*upward-3 > 0)
                                chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward-3)*128+(ox+x+lowestX)] = GenOre(oy+height*upward);
                        }
                        else if(upward == -1)
                        {
                            chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward)*128+(ox+x+lowestX)] = fill1;
                            if(oy+height*upward-1 > 0)
                                chunkData[(oz+z+lowestZ)*zSize+(oy+height*upward-1)*128+(ox+x+lowestX)] = fill3;
                        }
                    }
            }
        }
        for(z=0;z<(highestZ-lowestZ+1);++z)
        { // 패턴깎기
            count = 0;
            for(x=0;x<(highestX-lowestX+1);++x)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1 && count < lwidth)
                {
                    curpoints[z*(highestX-lowestX+1)+x] = 0;
                    count++;
                }
                if(count == lwidth)
                    break;
            }
            count = 0;
            for(x=(highestX-lowestX+1)-1;x>=0;--x)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1 && count < rwidth)
                {
                    curpoints[z*(highestX-lowestX+1)+x] = 0;
                    count++;
                }
                if(count == rwidth)
                    break;
            }
        }

        for(x=0;x<(highestX-lowestX+1);++x)
        { // 패턴깎기
            count = 0;
            for(z=0;z<(highestZ-lowestZ+1);++z)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1 && count < bwidth)
                {
                    curpoints[z*(highestX-lowestX+1)+x] = 0;
                    count++;
                }
                if(count == bwidth)
                    break;
            }
            count = 0;
            for(z=(highestZ-lowestZ+1)-1;z>=0;--z)
            {
                if(curpoints[z*(highestX-lowestX+1)+x] == 1 && count < twidth)
                {
                    curpoints[z*(highestX-lowestX+1)+x] = 0;
                    count++;
                }
                if(count == twidth)
                    break;
            }
        }



    }
    free(curpoints);
}
void FillMap(unsigned char *chunkData)
{
    // 음 여기서는 땅위를 모래, 풀숲, 그리고 땅높이를 결정하도록 하고 그냥 채운다.
    // 땅 높이도...terrain채우는 알고리즘으로 할까?
    int x,y,z, zSize=128*128,limit=128;
    // y값이 80미만이면 3으로 채우고 이상이면 0으로 채운다.
    srand(time(NULL));
    for(z=0;z<limit;++z)
    {
        for(y=0;y<limit;++y)
        {
            for(x=0;x<limit;++x)
            {
                if(y == 0)
                    chunkData[z*zSize+y*128+x] = BLOCK_INDESTRUCTABLE;
                else if(y == 63)
                    chunkData[z*zSize+y*128+x] = BLOCK_GRASS;
                else if(y < 63)
                    chunkData[z*zSize+y*128+x] = GenOre(y);
                else
                    chunkData[z*zSize+y*128+x] = 0;
            }
        }
    }

}

int IsOpaque(unsigned char block_id)
{
    if(block_id == BLOCK_EMPTY)
        return false;
    else
        return true;
}
int IsWaterGlass(unsigned char block_id)
{
    if(block_id == BLOCK_WATER || block_id == BLOCK_GLASS)
        return true;
    else
        return false;
}

void CalcRecursive(Chunk * chunk, Octree *octree, int x, int y, int z, int depth)
{
    int stride = 128;
    int i,j,k;
    for(i=0;i<depth;++i)
        stride /= 2;
    int notFilledFound = 0;
    int notFilledEmptyCount = 0;
    int waterGlassCount = 0;
    int partTrans = 0;
    // 이제 여기서 좀 비어도 X쪽으로는 블럭, Y쪽으로는 블럭, Z쪽으로는 블럭 등을 검사한다.
    // 기본적으로 지그재그로 꽉차있으면 블럭이다.
    // xz평면에서 y값 무시하고 꽉차있으면 y축으로 블럭이다.
    // 투명값이 좀 있어도 막혀있으면 막힌거
    int xblock[4]; // 왼쪽에서 +z를 오른쪽에 두고 -y를 아래에 두고 바라볼 때
    // 앞에서 봤을 때 [0] 위뒤 [1]위앞 [2]아래뒤 [3]아래앞
    int yblock[4]; // 위에서 -z를 위에 두고 +x를 오른쪽에 두고 바라볼 때
    // 앞에서 봤을 땐 [0] 왼뒤 [1] 오른뒤 [2]왼앞 [3] 오른앞
    int zblock[4]; // 앞에서 +x오른 +y위
    // [0] 왼위 [1] 오른위 [2] 왼아래 [3] 오른아래
    for(i=0;i<4;++i)
    {
        xblock[i] = 0;
        yblock[i] = 0;
        zblock[i] = 0;
    }

    int xfound;
    int yfound;
    int zfound;
    xfound = true;
    yfound = true;
    zfound = true;
    int xb[2][2];
    int yb[2][2];
    int zb[2][2];

    if(depth >= 7)
    {
        for(k=0;k<2;++k)
        {
            for(j=0;j<2;++j)
            {
                for(i=0;i<2;++i)
                {
                    if(!IsOpaque(chunk->chunk[((z+k)*128*128) + (y+j)*128 + x+i])) // empty
                    {
                        // 물이나 유리도 투명하지만, 오로지 주변에 물이나 유리, 빈공간이 있을 경우에만 그린다.
                        // 으... 옥트리에서 이건 어떻게 표현하나?
                        // COMPLETEWATER?
                        // PARTWATER?
                        notFilledFound = 1;
                        notFilledEmptyCount += 1;
                    }
                    else if(IsWaterGlass(chunk->chunk[((z+k)*128*128) + (y+j)*128 + x+i])) // transparent
                    {
                        waterGlassCount += 1;
                    }
                    else //opaque
                    {
                        if(i == 0 && j == 0 && k == 0) // 왼쪽아래뒷면
                        {
                            xblock[2] = 1;
                            yblock[0] = 1;
                            zblock[2] = 1;
                        }
                        else if(i == 1 && j == 0 && k == 0) // 오른쪽아래뒷면
                        {
                            xblock[2] = 1;
                            yblock[1] = 1;
                            zblock[3] = 1;
                        }
                        else if(i == 0 && j == 1 && k == 0) //왼쪽위뒤
                        {
                            xblock[0] = 1;
                            yblock[0] = 1;
                            zblock[0] = 1;
                        }
                        else if(i == 0 && j == 0 && k == 1) //왼쪽아래앞
                        {
                            xblock[3] = 1;
                            yblock[2] = 1;
                            zblock[2] = 1;
                        }
                        else if(i == 1 && j == 1 && k == 0) // 오른쪽위뒤
                        {
                            xblock[0] = 1;
                            yblock[1] = 1;
                            zblock[1] = 1;
                        }
                        else if(i == 0 && j == 1 && k == 1) // 왼쪽위앞
                        {
                            xblock[1] = 1;
                            yblock[2] = 1;
                            zblock[0] = 1;
                        }
                        else if(i == 1 && j == 0 && k == 1) // 오른쪽아래앞
                        {
                            xblock[3] = 1;
                            yblock[3] = 1;
                            zblock[3] = 1;
                        }
                        else if(i == 1 && j == 1 && k == 1) // 오른쪽위앞
                        {
                            xblock[1] = 1;
                            yblock[3] = 1;
                            zblock[1] = 1;
                        }
                    }
                }
            }
        }

        if(notFilledEmptyCount == 8)
        {
            octree->filled = OT_EMPTY;
        }
        else if(notFilledFound == 1)
        {
            octree->filled = OT_HALFFILLED;
        }
        else
        {
            octree->filled = OT_FILLED;
        }

        if(waterGlassCount == 8)
        {
            octree->filled = OT_COMPLETETRANSPARENT;
        }
        else if(waterGlassCount > 0)
        {
            octree->filled |= OT_PARTTRANSPARENT;
        }

        for(i=0;i<4;++i)
        {
            if(xblock[i] == 0)
                xfound = false;
            if(yblock[i] == 0)
                yfound = false;
            if(zblock[i] == 0)
                zfound = false;
        }
        if(xfound)
            octree->filled |= OT_XBLOCK;
        if(yfound)
            octree->filled |= OT_YBLOCK;
        if(zfound)
            octree->filled |= OT_ZBLOCK;

    }
    else
    {
        for(j=0;j<2;++j)
        {
            for(i=0;i<2;++i)
            {
                xb[i][j] = 0;
                yb[i][j] = 0;
                zb[i][j] = 0;
            }
        }
        if(octree->children) // 사실 이건 필요가 없음
        {
            for(k=0;k<2;++k)
            {
                for(j=0;j<2;++j)
                {
                    for(i=0;i<2;++i)
                    {
                        CalcRecursive(chunk, octree->children[k*2*2+j*2+i], x+(i*stride), y+(j*stride), z+(k*stride), depth+1);
                    }
                }
            }

            for(k=0;k<2;++k)
            {
                for(j=0;j<2;++j)
                {
                    for(i=0;i<2;++i)
                    {
                        if(octree->children[k*2*2+j*2+i]->filled & OT_HALFFILLED)
                            notFilledFound = 1;
                        else if(octree->children[k*2*2+j*2+i]->filled & OT_EMPTY)
                        {
                            notFilledEmptyCount += 1;
                            notFilledFound = 1;
                        }
                        if(octree->children[k*2*2+j*2+i]->filled & OT_FILLED)
                            ;
                        else
                            notFilledFound = 1;
                        if(octree->children[k*2*2+j*2+i]->filled & OT_PARTTRANSPARENT)
                            partTrans = 1;
                        else if(octree->children[k*2*2+j*2+i]->filled & OT_COMPLETETRANSPARENT)
                            waterGlassCount += 1;

                        // xblock이 각기 서로 다른 j,k값에서 다 나오기만 하면 된다.
                        if(octree->children[k*2*2+j*2+i]->filled & OT_XBLOCK)
                            xb[j][k] = 1;
                        if(octree->children[k*2*2+j*2+i]->filled & OT_YBLOCK)
                            yb[i][k] = 1;
                        if(octree->children[k*2*2+j*2+i]->filled & OT_ZBLOCK)
                            zb[i][j] = 1;
                    }
                }
            }

            if(notFilledFound == 1)
            {
                if(notFilledEmptyCount == 8)
                    octree->filled = OT_EMPTY;
                else
                    octree->filled = OT_HALFFILLED;
            }
            else
                octree->filled = OT_FILLED;


            if(waterGlassCount == 8)
                octree->filled = OT_COMPLETETRANSPARENT;
            else if(waterGlassCount > 0 || partTrans)
                octree->filled |= OT_PARTTRANSPARENT;

            for(j=0;j<2;++j)
            {
                for(i=0;i<2;++i)
                {
                    if(xb[i][j] == 0)
                        xfound = false;
                    if(yb[i][j] == 0)
                        yfound = false;
                    if(zb[i][j] == 0)
                        zfound = false;
                }
            }

            if(xfound)
                octree->filled |= OT_XBLOCK;
            if(yfound)
                octree->filled |= OT_YBLOCK;
            if(zfound)
                octree->filled |= OT_ZBLOCK;
        }
    }
}


int IsPolyFront2(float quads[12], float vx, float vy, float vz)
{
    XYZ a, b, c;
    a.x = quads[0];
    a.y = quads[1];
    a.z = quads[2];
    b.x = quads[3];
    b.y = quads[4];
    b.z = quads[5];
    c.x = quads[6];
    c.y = quads[7];
    c.z = quads[8];
    XYZ ba, ca;
    XYZ n;
    ba.x = b.x-a.x;
    ba.y = b.y-a.y;
    ba.z = b.z-a.z;
    ca.x = c.x-a.x;
    ca.y = c.y-a.y;
    ca.z = c.z-a.z;
    float len;
    len = sqrt(ba.x*ba.x+ba.y*ba.y+ba.z*ba.z);
    if(len < 0.0001)
        len = 0.0001;
    ba.x = ba.x/len;
    ba.y = ba.y/len;
    ba.z = ba.z/len;

    len = sqrt(ca.x*ca.x+ca.y*ca.y+ca.z*ca.z);
    if(len < 0.0001)
        len = 0.0001;
    ca.x = ca.x/len;
    ca.y = ca.y/len;
    ca.z = ca.z/len;

    n.x = ba.y*ca.z-ba.z*ca.y;
    n.y = ba.z*ca.x-ba.x*ca.z;
    n.z = ba.x*ca.y-ba.y*ca.x;
    len = sqrt(n.x*n.x+n.y*n.y+n.z*n.z);
    if(len < 0.0001)
        len = 0.0001;
    n.x = n.x/len;
    n.y = n.y/len;
    n.z = n.z/len;

    XYZ view;
    view.x = vx-a.x;
    view.y = vy-a.y;
    view.z = vz-a.z;
    len = sqrt(view.x*view.x+view.y*view.y+view.z*view.z);
    if(len < 0.0001)
        len = 0.0001;
    view.x = view.x/len;
    view.y = view.y/len;
    view.z = view.z/len;

    float dot = n.x*view.x+n.y*view.y+n.z*view.z;
    if(dot >= 0)
        return true;
    else
        return false;
}

int IsPolyFront(int place, int x, int y, int z, float vx, float vy, float vz)
{
    /*
            nxa[0] = 0
            nya[0] = -1
            nza[0] = 0
            nxa[1] = 0
            nya[1] = 1
            nza[1] = 0
            nxa[2] = -1
            nya[2] = 0
            nza[2] = 0
            nxa[3] = 1
            nya[3] = 0
            nza[3] = 0
            nxa[4] = 0
            nya[4] = 0
            nza[4] = -1
            nxa[5] = 0
            nya[5] = 0
            nza[5] = 1

    기본적으로 x,y,z를 기준으로 하여 모든 좌표가 증가하기만 하는 구조로 되어있다.
    그러므로 뒷쪽, 왼쪽, 아래를 기준으로 하여 증가한다.
    */
    // 일단 노멀을 만들어서 뒷면테스트부터 한다.
    // 폴리곤의 첫번째 버텍스에서 노멀을 만들고,
    // 뷰와 닷한다.
    float ox,oy,oz;
    float nx,ny,nz;
    float len;
    float dotted;
    if(place == 1) { // 윗면, 위에서 봤을 때 반시계방향으로 그린다.
        ox = (float)x; // 왼쪽
        oy = (float)y+1.0f; // 위
        oz = (float)z; // 뒷쪽(화면 깊은쪽)
        nx = 0.001f;
        ny = 1.0f;
        nz = 0.001f;
    }
    else if(place == 0) { // 아랫면, 아래에서 봤을 때 반시계방향으로 그린다.
        ox = (float)x; // 왼쪽
        oy = (float)y; // 아래
        oz = (float)z; // 뒷쪽(화면 깊은쪽)
        nx = 0.001f;
        ny = -1.0f;
        nz = 0.001f;
    }
    else if(place == 2) { // 왼쪽면, 왼쪽에서 봤을 때 반시계방향으로 그린다.
        ox = (float)x; // 왼쪽
        oy = (float)y; // 아래
        oz = (float)z; // 뒷쪽(화면 깊은쪽)
        nx = -1.0f;
        ny = 0.001f;
        nz = 0.001f;
    }
    else if(place == 3) { // 오른쪽면, 오른쪽에서 봤을 때 반시계방향으로 그린다.
        ox = (float)x+1.0f; // 오른쪽
        oy = (float)y; // 아래
        oz = (float)z; // 뒷쪽(화면 깊은쪽)
        nx = 1.0f;
        ny = 0.001f;
        nz = 0.001f;
    }
    else if(place == 4) { // 뒷면, 뒷쪽에서 봤을 때 반시계방향으로 그린다. 앞에서 봤을 때 시계방향임
        ox = (float)x; // 왼쪽
        oy = (float)y; // 아래
        oz = (float)z; // 뒷쪽(화면 깊은쪽)
        nx = 0.001f;
        ny = 0.001f;
        nz = -1.0f;
    }
    else if(place == 5) { // 앞면, 앞쪽에서 봤을 때 반시계방향으로 그린다.
        ox = (float)x; // 왼쪽
        oy = (float)y; // 아래
        oz = (float)z+1.0f; // 앞쪽(화면 얕은쪽)
        nx = 0.001f;
        ny = 0.001f;
        nz = 1.0f;
    }

    vx = vx-ox;
    vy = vy-oy;
    vz = vz-oz;
    len = sqrt(nx*nx+ny*ny+nz*nz);
    if(len == 0.0)
        return true;
    nx /= len;
    ny /= len;
    nz /= len;
    len = sqrt(vx*vx+vy*vy+vz*vz);
    if(len == 0.0)
        return true;
    vx /= len;
    vy /= len;
    vz /= len;
    dotted = nx*vx+ny*vy+nz*vz;
    if(dotted >= 0)
        return true;
    else
        return false;
}

void FillTex(float *quadBuffer, int place, unsigned char block)
{
    /*
            nxa[0] = 0
            nya[0] = -1
            nza[0] = 0
            nxa[1] = 0
            nya[1] = 1
            nza[1] = 0
            nxa[2] = -1
            nya[2] = 0
            nza[2] = 0
            nxa[3] = 1
            nya[3] = 0
            nza[3] = 0
            nxa[4] = 0
            nya[4] = 0
            nza[4] = -1
            nxa[5] = 0
            nya[5] = 0
            nza[5] = 1
    */

    int coords[256*2*3] = {0,0, 0,0, 0,0,
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
        9,4, 9,4, 9,4, // 10
        7,4, 7,4, 7,4,
        10,4, 10,4, 10,4,
        11,4, 11,4, 11,4,
        0,0, 0,0, 0,0, // panelswitch
        0,0, 0,0, 0,0,
        0,0, 0,0, 0,0,
        0,0, 0,0, 0,0,
        0,0, 0,0, 0,0, // 10
        0,0, 0,0, 0,0, // 10

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
        8,4, 8,4, 8,4, // 10
    };
    // 256블럭, x,y, 위면 옆면 아래면
    /*
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
     */
    float texupx = (coords[block*2*3 + 0]*32.0f) / 512.0f;
    float texupy = (coords[block*2*3 + 1]*32.0f) / 512.0f;
    float texmidx = (coords[block*2*3 + 2]*32.0f) / 512.0f;
    float texmidy = (coords[block*2*3 + 3]*32.0f) / 512.0f;
    float texbotx = (coords[block*2*3 + 4]*32.0f) / 512.0f;
    float texboty = (coords[block*2*3 + 5]*32.0f) / 512.0f;

    float orgx, offx, orgy, offy;
    if(place == 1) { // 윗면, 위에서 봤을 때 반시계방향으로 그린다.
        orgx = texupx;
        offx = texupx+(32.0f/512.0f);
        offy = texupy;
        orgy = texupy+(32.0f/512.0f);
        quadBuffer[0*2+0] = (float)orgx; // 왼뒤
        quadBuffer[0*2+1] = (float)offy;

        quadBuffer[1*2+0] = (float)orgx; // 왼앞
        quadBuffer[1*2+1] = (float)orgy;

        quadBuffer[2*2+0] = (float)offx; // 오앞
        quadBuffer[2*2+1] = (float)orgy;

        quadBuffer[3*2+0] = (float)offx; // 오뒤
        quadBuffer[3*2+1] = (float)offy;
    }
    else if(place == 0) { // 아랫면, 아래에서 봤을 때 반시계방향으로 그린다.
        orgx = texbotx;
        offx = texbotx+(32.0f/512.0f);
        offy = texboty;
        orgy = texboty+(32.0f/512.0f);
        quadBuffer[0*2+0] = (float)orgx; // 왼뒤
        quadBuffer[0*2+1] = (float)orgy;

        quadBuffer[1*2+0] = (float)offx; // 오뒤
        quadBuffer[1*2+1] = (float)orgy;

        quadBuffer[2*2+0] = (float)offx; // 오앞
        quadBuffer[2*2+1] = (float)offy;

        quadBuffer[3*2+0] = (float)orgx; // 왼앞
        quadBuffer[3*2+1] = (float)offy;
    }
    else if(place == 2) { // 왼쪽면, 왼쪽에서 봤을 때 반시계방향으로 그린다.
        orgx = texmidx;
        offx = texmidx+(32.0f/512.0f);
        offy = texmidy;
        orgy = texmidy+(32.0f/512.0f);
        quadBuffer[0*2+0] = (float)orgx; // 아뒤
        quadBuffer[0*2+1] = (float)orgy; //

        quadBuffer[1*2+0] = (float)offx; // 아앞
        quadBuffer[1*2+1] = (float)orgy; //

        quadBuffer[2*2+0] = (float)offx; // 위앞
        quadBuffer[2*2+1] = (float)offy; //

        quadBuffer[3*2+0] = (float)orgx; //
        quadBuffer[3*2+1] = (float)offy; //
    }
    else if(place == 3) { // 오른쪽면, 오른쪽에서 봤을 때 반시계방향으로 그린다.
        orgx = texmidx;
        offx = texmidx+(32.0f/512.0f);
        offy = texmidy;
        orgy = texmidy+(32.0f/512.0f);
        quadBuffer[0*2+0] = (float)offx; // 아뒤
        quadBuffer[0*2+1] = (float)orgy; //

        quadBuffer[1*2+0] = (float)offx; //
        quadBuffer[1*2+1] = (float)offy; //

        quadBuffer[2*2+0] = (float)orgx; //
        quadBuffer[2*2+1] = (float)offy; //

        quadBuffer[3*2+0] = (float)orgx;
        quadBuffer[3*2+1] = (float)orgy;
    }
    else if(place == 4) { // 뒷면, 뒷쪽에서 봤을 때 반시계방향으로 그린다. 앞에서 봤을 때 시계방향임
        orgx = texmidx;
        offx = texmidx+(32.0f/512.0f);
        offy = texmidy;
        orgy = texmidy+(32.0f/512.0f);
        quadBuffer[0*2+0] = (float)offx; //
        quadBuffer[0*2+1] = (float)orgy; //
        quadBuffer[1*2+0] = (float)offx; //
        quadBuffer[1*2+1] = (float)offy; //
        quadBuffer[2*2+0] = (float)orgx; // 왼위
        quadBuffer[2*2+1] = (float)offy; //
        quadBuffer[3*2+0] = (float)orgx; // 왼아래
        quadBuffer[3*2+1] = (float)orgy;



    }
    else if(place == 5) { // 앞면, 앞쪽에서 봤을 때 반시계방향으로 그린다.
        orgx = texmidx;
        offx = texmidx+(32.0f/512.0f);
        offy = texmidy;
        orgy = texmidy+(32.0f/512.0f);
        quadBuffer[0*2+0] = (float)orgx; // 왼쪽
        quadBuffer[0*2+1] = (float)orgy; // 아래

        quadBuffer[1*2+0] = (float)offx; //
        quadBuffer[1*2+1] = (float)orgy; //

        quadBuffer[2*2+0] = (float)offx; //
        quadBuffer[2*2+1] = (float)offy; //

        quadBuffer[3*2+0] = (float)orgx; //
        quadBuffer[3*2+1] = (float)offy; //
    }
}

void GenNormal(float *quadBuffer, int place)
{
    /*
            nxa[0] = 0
            nya[0] = -1
            nza[0] = 0
            nxa[1] = 0
            nya[1] = 1
            nza[1] = 0
            nxa[2] = -1
            nya[2] = 0
            nza[2] = 0
            nxa[3] = 1
            nya[3] = 0
            nza[3] = 0
            nxa[4] = 0
            nya[4] = 0
            nza[4] = -1
            nxa[5] = 0
            nya[5] = 0
            nza[5] = 1

    기본적으로 x,y,z를 기준으로 하여 모든 좌표가 증가하기만 하는 구조로 되어있다.
    그러므로 뒷쪽, 왼쪽, 아래를 기준으로 하여 증가한다.
    */
    // 일단 노멀을 만들어서 뒷면테스트부터 한다.
    // 폴리곤의 첫번째 버텍스에서 노멀을 만들고,
    // 뷰와 닷한다.
    float nx,ny,nz;
    if(place == 1) { // 윗면, 위에서 봤을 때 반시계방향으로 그린다.
        nx = 0.0f;
        ny = 1.0f;
        nz = 0.0f;
    }
    else if(place == 0) { // 아랫면, 아래에서 봤을 때 반시계방향으로 그린다.
        nx = 0.0f;
        ny = -1.0f;
        nz = 0.0f;
    }
    else if(place == 2) { // 왼쪽면, 왼쪽에서 봤을 때 반시계방향으로 그린다.
        nx = -1.0f;
        ny = 0.0f;
        nz = 0.0f;
    }
    else if(place == 3) { // 오른쪽면, 오른쪽에서 봤을 때 반시계방향으로 그린다.
        nx = 1.0f;
        ny = 0.0f;
        nz = 0.0f;
    }
    else if(place == 4) { // 뒷면, 뒷쪽에서 봤을 때 반시계방향으로 그린다. 앞에서 봤을 때 시계방향임
        nx = 0.0f;
        ny = 0.0f;
        nz = -1.0f;
    }
    else if(place == 5) { // 앞면, 앞쪽에서 봤을 때 반시계방향으로 그린다.
        nx = 0.0f;
        ny = 0.0f;
        nz = 1.0f;
    }
    int i;
    for(i=0;i<4;++i)
    {
        quadBuffer[i*3+0] = nx; // 왼쪽
        quadBuffer[i*3+1] = ny; // 아래
        quadBuffer[i*3+2] = nz; // 앞쪽(화면 얕은쪽)
    }
}
void GenQuad(float *quadBuffer, int place, int x, int y, int z)
{
    /*
            nxa[0] = 0
            nya[0] = -1
            nza[0] = 0
            nxa[1] = 0
            nya[1] = 1
            nza[1] = 0
            nxa[2] = -1
            nya[2] = 0
            nza[2] = 0
            nxa[3] = 1
            nya[3] = 0
            nza[3] = 0
            nxa[4] = 0
            nya[4] = 0
            nza[4] = -1
            nxa[5] = 0
            nya[5] = 0
            nza[5] = 1

    기본적으로 x,y,z를 기준으로 하여 모든 좌표가 증가하기만 하는 구조로 되어있다.
    그러므로 뒷쪽, 왼쪽, 아래를 기준으로 하여 증가한다.
    */
    // 일단 노멀을 만들어서 뒷면테스트부터 한다.
    // 폴리곤의 첫번째 버텍스에서 노멀을 만들고,
    // 뷰와 닷한다.
    if(place == 1) { // 윗면, 위에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y+1.0f; // 위
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)

        quadBuffer[1*3+0] = (float)x; // 왼쪽
        quadBuffer[1*3+1] = (float)y+1.0f;
        quadBuffer[1*3+2] = (float)z+1.0f; // 앞쪽

        quadBuffer[2*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[2*3+1] = (float)y+1.0f;
        quadBuffer[2*3+2] = (float)z+1.0f; // 앞쪽

        quadBuffer[3*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[3*3+1] = (float)y+1.0f;
        quadBuffer[3*3+2] = (float)z; // 뒷쪽
    }
    else if(place == 0) { // 아랫면, 아래에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)

        quadBuffer[1*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[1*3+1] = (float)y;
        quadBuffer[1*3+2] = (float)z; // 뒷쪽

        quadBuffer[2*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[2*3+1] = (float)y;
        quadBuffer[2*3+2] = (float)z+1.0f; // 앞쪽

        quadBuffer[3*3+0] = (float)x; // 왼쪽
        quadBuffer[3*3+1] = (float)y;
        quadBuffer[3*3+2] = (float)z+1.0f; // 앞쪽
    }
    else if(place == 2) { // 왼쪽면, 왼쪽에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)

        quadBuffer[1*3+0] = (float)x; //
        quadBuffer[1*3+1] = (float)y; //
        quadBuffer[1*3+2] = (float)z+1.0f; //

        quadBuffer[2*3+0] = (float)x; //
        quadBuffer[2*3+1] = (float)y+1.0f; //
        quadBuffer[2*3+2] = (float)z+1.0f; //

        quadBuffer[3*3+0] = (float)x; //
        quadBuffer[3*3+1] = (float)y+1.0f; //
        quadBuffer[3*3+2] = (float)z; //
    }
    else if(place == 3) { // 오른쪽면, 오른쪽에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)

        quadBuffer[1*3+0] = (float)x+1.0f; //
        quadBuffer[1*3+1] = (float)y+1.0f; //
        quadBuffer[1*3+2] = (float)z; //

        quadBuffer[2*3+0] = (float)x+1.0f; //
        quadBuffer[2*3+1] = (float)y+1.0f; //
        quadBuffer[2*3+2] = (float)z+1.0f; //

        quadBuffer[3*3+0] = (float)x+1.0f; //
        quadBuffer[3*3+1] = (float)y; //
        quadBuffer[3*3+2] = (float)z+1.0f; //
    }
    else if(place == 4) { // 뒷면, 뒷쪽에서 봤을 때 반시계방향으로 그린다. 앞에서 봤을 때 시계방향임
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)

        quadBuffer[1*3+0] = (float)x; //
        quadBuffer[1*3+1] = (float)y+1.0f; //
        quadBuffer[1*3+2] = (float)z; //

        quadBuffer[2*3+0] = (float)x+1.0f; //
        quadBuffer[2*3+1] = (float)y+1.0f; //
        quadBuffer[2*3+2] = (float)z; //

        quadBuffer[3*3+0] = (float)x+1.0f; //
        quadBuffer[3*3+1] = (float)y; //
        quadBuffer[3*3+2] = (float)z; //
    }
    else if(place == 5) { // 앞면, 앞쪽에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z+1.0f; // 앞쪽(화면 얕은쪽)

        quadBuffer[1*3+0] = (float)x+1.0f; //
        quadBuffer[1*3+1] = (float)y; //
        quadBuffer[1*3+2] = (float)z+1.0f; //

        quadBuffer[2*3+0] = (float)x+1.0f; //
        quadBuffer[2*3+1] = (float)y+1.0f; //
        quadBuffer[2*3+2] = (float)z+1.0f; //

        quadBuffer[3*3+0] = (float)x; //
        quadBuffer[3*3+1] = (float)y+1.0f; //
        quadBuffer[3*3+2] = (float)z+1.0f; //
    }
}

Octree *AccessRecur(Octree *parent, int curx, int cury, int curz, int targetx, int targety, int targetz, int depth, int targetdepth)
{
    // target좌표나 curx좌표는 맵 좌표가 아닌 옥트리 로컬 좌표여야 한다. 기본적으로 2x2x2를 리턴하므로 targetx등을 포함하는 2x2x2를 가진 옥트리가 리턴된다.
    int dx, dy, dz;
    int octx,octy,octz;
    int newx,newy,newz;
    int stride = 128;
    int i;
    for(i=0;i<depth;++i)
        stride /= 2;

    if(depth == targetdepth)
        return parent;
    else
    {
        dx = targetx-curx;
        dy = targety-cury;
        dz = targetz-curz;
        if(dx >= stride) {
            octx = 1;
            newx = curx+stride;
        }
        else {
            octx = 0;
            newx = curx;
        }

        if(dy >= stride) {
            octy = 1;
            newy = cury+stride;
        }
        else {
            octy = 0;
            newy = cury;
        }

        if(dz >= stride) {
            octz = 1;
            newz = curz+stride;
        }
        else {
            octz = 0;
            newz = curz;
        }
        return AccessRecur(parent->children[octz*2*2 + octy*2 + octx], newx,newy,newz, targetx,targety,targetz,depth+1,targetdepth);
        //8개 좌표중에 하나를 선택하는 것이다.
    }
}

Octree *AccessOctreeWithXYZ(Octree * root, int x, int y, int z, int targetdepth)
{
    return AccessRecur(root, 0,0,0,x,y,z,1, targetdepth);
}
int SphereInFrustum(double x, double y, double z, double radius, double frustum[6][4])
{
    int p;
    for(p=0;p<6;++p)
    {
        if(frustum[p][0] * x + frustum[p][1] * y + frustum[p][2] * z + frustum[p][3] <= -radius)
            return false;
    }
    return true;
}

int CubeInFrustum(float x, float y, float z, double size, double frustum[6][4])
{
    int p;
    int c;
    int c2;
    c2 = 0;

    for(p=0; p < 6; ++p)
    {
        c = 0;
        if((frustum[p][0] * (x - size) + frustum[p][1] * (y - size) + frustum[p][2] * (z - size) + frustum[p][3]) >= 0)
            c += 1;
        if((frustum[p][0] * (x + size) + frustum[p][1] * (y - size) + frustum[p][2] * (z - size) + frustum[p][3]) >= 0)
            c += 1;
        if((frustum[p][0] * (x - size) + frustum[p][1] * (y + size) + frustum[p][2] * (z - size) + frustum[p][3]) >= 0)
            c += 1;
        if((frustum[p][0] * (x + size) + frustum[p][1] * (y + size) + frustum[p][2] * (z - size) + frustum[p][3]) >= 0)
            c += 1;
        if((frustum[p][0] * (x - size) + frustum[p][1] * (y - size) + frustum[p][2] * (z + size) + frustum[p][3]) >= 0)
            c += 1;
        if((frustum[p][0] * (x + size) + frustum[p][1] * (y - size) + frustum[p][2] * (z + size) + frustum[p][3]) >= 0)
            c += 1;
        if((frustum[p][0] * (x - size) + frustum[p][1] * (y + size) + frustum[p][2] * (z + size) + frustum[p][3]) >= 0)
            c += 1;
        if((frustum[p][0] * (x + size) + frustum[p][1] * (y + size) + frustum[p][2] * (z + size) + frustum[p][3]) >= 0)
            c += 1;
        if(c == 0)
            return 0;
        if(c == 8)
            c2 += 1;
    }
    if(c2 == 6)
        return 2;
    else
        return 1;
}

void FillHeights(Chunk *chunk)
{
    int i,j,k;
    int zSize = 128*128;
    memset(chunk->heights, 0, sizeof(unsigned char)*128*128);
    for(k=0;k < 128;++k)
    {
        for(j=127;j >= 0;--j)
        {
            for(i=0;i < 128;++i)
            {
                char b = chunk->chunk[k*zSize+j*128+i];
                if(b != BLOCK_CHEST && b != BLOCK_WATER && b != BLOCK_GLASS && b != BLOCK_EMPTY && chunk->heights[k*128+i] < j) // XX: 물인지 아닌지를 보야
                {
                    chunk->heights[k*128+i] = j;
                }
            }
        }
    }
}

void FillColor(int x, int y, int z, int face, unsigned char *out, float sunStr[9], Extra *extras[27])
{
    // extras에서 토치를 읽어옴
    int i,j,k, face2;
    float quadBuffer[12],xxx,yyy,zzz, nx,ny,nz,length, dot, sunStrs[4];
    int colors[4];
    if(face == 1) { // 윗면, 위에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y+1.0f; // 위
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)
        sunStrs[0] = (sunStr[0]+sunStr[1]+sunStr[2]+sunStr[4])/4.0f;

        quadBuffer[1*3+0] = (float)x; // 왼쪽
        quadBuffer[1*3+1] = (float)y+1.0f;
        quadBuffer[1*3+2] = (float)z+1.0f; // 앞쪽
        sunStrs[1] = (sunStr[0]+sunStr[6]+sunStr[7]+sunStr[4])/4.0f;

        quadBuffer[2*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[2*3+1] = (float)y+1.0f;
        quadBuffer[2*3+2] = (float)z+1.0f; // 앞쪽
        sunStrs[2] = (sunStr[0]+sunStr[7]+sunStr[8]+sunStr[5])/4.0f;

        quadBuffer[3*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[3*3+1] = (float)y+1.0f;
        quadBuffer[3*3+2] = (float)z; // 뒷쪽
        sunStrs[3] = (sunStr[0]+sunStr[2]+sunStr[3]+sunStr[5])/4.0f;
    }
    else if(face == 0) { // 아랫면, 아래에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)
        sunStrs[0] = (sunStr[0]+sunStr[1]+sunStr[2]+sunStr[4])/4.0001f;

        quadBuffer[1*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[1*3+1] = (float)y;
        quadBuffer[1*3+2] = (float)z; // 뒷쪽
        sunStrs[1] = (sunStr[0]+sunStr[2]+sunStr[3]+sunStr[5])/4.0001f;

        quadBuffer[2*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[2*3+1] = (float)y;
        quadBuffer[2*3+2] = (float)z+1.0f; // 앞쪽
        sunStrs[2] = (sunStr[0]+sunStr[7]+sunStr[8]+sunStr[5])/4.0001f;

        quadBuffer[3*3+0] = (float)x; // 왼쪽
        quadBuffer[3*3+1] = (float)y;
        quadBuffer[3*3+2] = (float)z+1.0f; // 앞쪽
        sunStrs[3] = (sunStr[0]+sunStr[6]+sunStr[7]+sunStr[4])/4.0001f;
    }
    else if(face == 2) { // 왼쪽면, 왼쪽에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)
        sunStrs[0] = (sunStr[0]+sunStr[1]+sunStr[2]+sunStr[4])/4.0001f;

        quadBuffer[1*3+0] = (float)x; //
        quadBuffer[1*3+1] = (float)y; //
        quadBuffer[1*3+2] = (float)z+1.0f; // 앞쪽
        sunStrs[1] = (sunStr[0]+sunStr[6]+sunStr[7]+sunStr[4])/4.0001f;

        quadBuffer[2*3+0] = (float)x; //
        quadBuffer[2*3+1] = (float)y+1.0f; //
        quadBuffer[2*3+2] = (float)z+1.0f; //
        sunStrs[2] = (sunStr[0]+sunStr[6]+sunStr[7]+sunStr[4])/4.0f;

        quadBuffer[3*3+0] = (float)x; //
        quadBuffer[3*3+1] = (float)y+1.0f; //
        quadBuffer[3*3+2] = (float)z; //
        sunStrs[3] = (sunStr[0]+sunStr[1]+sunStr[2]+sunStr[4])/4.0f;
    }
    else if(face == 3) { // 오른쪽면, 오른쪽에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x+1.0f; // 오른쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)
        sunStrs[0] = (sunStr[0]+sunStr[2]+sunStr[3]+sunStr[5])/4.0001f;

        quadBuffer[1*3+0] = (float)x+1.0f; //
        quadBuffer[1*3+1] = (float)y+1.0f; //
        quadBuffer[1*3+2] = (float)z; //
        sunStrs[1] = (sunStr[0]+sunStr[2]+sunStr[3]+sunStr[5])/4.0f;

        quadBuffer[2*3+0] = (float)x+1.0f; //
        quadBuffer[2*3+1] = (float)y+1.0f; //
        quadBuffer[2*3+2] = (float)z+1.0f; //
        sunStrs[2] = (sunStr[0]+sunStr[7]+sunStr[8]+sunStr[5])/4.0f;

        quadBuffer[3*3+0] = (float)x+1.0f; //
        quadBuffer[3*3+1] = (float)y; //
        quadBuffer[3*3+2] = (float)z+1.0f; //
        sunStrs[3] = (sunStr[0]+sunStr[7]+sunStr[8]+sunStr[5])/4.0001f;
    }
    else if(face == 4) { // 뒷면, 뒷쪽에서 봤을 때 반시계방향으로 그린다. 앞에서 봤을 때 시계방향임
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z; // 뒷쪽(화면 깊은쪽)
        sunStrs[0] = (sunStr[0]+sunStr[1]+sunStr[2]+sunStr[4])/4.0001f;

        quadBuffer[1*3+0] = (float)x; //
        quadBuffer[1*3+1] = (float)y+1.0f; //
        quadBuffer[1*3+2] = (float)z; //
        sunStrs[1] = (sunStr[0]+sunStr[1]+sunStr[2]+sunStr[4])/4.0f;

        quadBuffer[2*3+0] = (float)x+1.0f; //
        quadBuffer[2*3+1] = (float)y+1.0f; //
        quadBuffer[2*3+2] = (float)z; //
        sunStrs[2] = (sunStr[0]+sunStr[2]+sunStr[3]+sunStr[5])/4.0f;

        quadBuffer[3*3+0] = (float)x+1.0f; //
        quadBuffer[3*3+1] = (float)y; //
        quadBuffer[3*3+2] = (float)z; //
        sunStrs[3] = (sunStr[0]+sunStr[2]+sunStr[3]+sunStr[5])/4.0001f;
    }
    else if(face == 5) { // 앞면, 앞쪽에서 봤을 때 반시계방향으로 그린다.
        quadBuffer[0*3+0] = (float)x; // 왼쪽
        quadBuffer[0*3+1] = (float)y; // 아래
        quadBuffer[0*3+2] = (float)z+1.0f; // 앞쪽(화면 얕은쪽)
        sunStrs[0] = (sunStr[0]+sunStr[6]+sunStr[7]+sunStr[4])/4.0001f;

        quadBuffer[1*3+0] = (float)x+1.0f; //
        quadBuffer[1*3+1] = (float)y; //
        quadBuffer[1*3+2] = (float)z+1.0f; //
        sunStrs[1] = (sunStr[0]+sunStr[7]+sunStr[8]+sunStr[5])/4.0001f;

        quadBuffer[2*3+0] = (float)x+1.0f; //
        quadBuffer[2*3+1] = (float)y+1.0f; //
        quadBuffer[2*3+2] = (float)z+1.0f; //
        sunStrs[2] = (sunStr[0]+sunStr[7]+sunStr[8]+sunStr[5])/4.0f;

        quadBuffer[3*3+0] = (float)x; //
        quadBuffer[3*3+1] = (float)y+1.0f; //
        quadBuffer[3*3+2] = (float)z+1.0f; //
        sunStrs[3] = (sunStr[0]+sunStr[6]+sunStr[7]+sunStr[4])/4.0f;
    }
    if(face == 0)
    {
        nx = 0.0f;
        ny = -1.0f;
        nz = 0.0f;
    }
    else if(face == 1)
    {
        nx = 0.0f;
        ny = 1.0f;
        nz = 0.0f;
    }
    else if(face == 2)
    {
        nx = -1.0f;
        ny = 0.0f;
        nz = 0.0f;
    }
    else if(face == 3)
    {
        nx = 1.0f;
        ny = 0.0f;
        nz = 0.0f;
    }
    else if(face == 4)
    {
        nx = 0.0f;
        ny = 0.0f;
        nz = -1.0f;
    }
    else if(face == 5)
    {
        nx = 0.0f;
        ny = 0.0f;
        nz = 1.0f;
    }
    for(k=0;k<4;++k)
    {
        colors[k] = (unsigned char)(255.0f*sunStrs[k]*0.6f);
    }
    for(i=0; i<27;++i)
    {
        if(extras[i])
        {
            for(j=0;j<extras[i]->torchIdx;++j)
            {
                for(k=0;k<4;++k)
                {
                    xxx = (float)extras[i]->torches[j].x;
                    yyy = (float)extras[i]->torches[j].y;
                    zzz = (float)extras[i]->torches[j].z;
                    xxx -= quadBuffer[k*3];
                    yyy -= quadBuffer[k*3+1];
                    zzz -= quadBuffer[k*3+2];
                    length = sqrt(xxx*xxx+yyy*yyy+zzz*zzz);
                    xxx /= length;
                    yyy /= length;
                    zzz /= length;
                    if(length == 0.0f)
                        length = 0.0001f;
                    face2 = extras[i]->torches[j].face;
                    dot = xxx*nx+yyy*ny+zzz*nz;
                    dot = ABS(dot);
                    if(dot < 0.5f)
                        dot = 1.0f-0.5f;
                    if(extras[i]->torches[j].x == x && extras[i]->torches[j].y == y && extras[i]->torches[j].z == z)
                        dot = 1.0f;
                    if(length < 4.0f)
                    {
                        colors[k] += (unsigned char)(255.0f*((4.0f-length)/4.0f)*dot);
                        if(colors[k] > 255)
                            colors[k] = 255;
                    }
                }
            }
        }
    }
    for(i=0; i<4; ++i)
    {
        out[i*3] = colors[i];
        out[i*3+1] = colors[i];
        out[i*3+2] = colors[i];
    }
}

float SunLit(int place, int blockingBlocks, int curFaceOpen)
{
    float rad;
    if(place == 0 || place == 1)
        rad = 9.0f;
    else
        rad = 6.2f;
    float sunStr = ((float)rad*(float)rad-(float)blockingBlocks)/((float)rad*(float)rad);
    if(curFaceOpen)
    {
        sunStr = 1.0f;
    }
    return sunStr;
}
int DirectionCheck(int place, int x, int z)
{
    if(place == 0) // 아래
    {
        return true;
    }
    else if(place == 1) // 위
    {
        return true;
    }
    else if(place == 2) // 왼쪽
    {
        if(x < 4)
            return true;
    }
    else if(place == 3) // 오른쪽 3, 5에서 에러남. 오른/앞. 또는 2,4가 에러일수도?
    {
        if(x > 4)
            return true;
    }
    else if(place == 4) // 뒷 
    {
        if(z < 4)
            return true;
    }
    else if(place == 5) // 앞
    {
        if(z > 4)
            return true;
    }
    return false;
}
int TestSunLit(int x, int y, int z, Chunk *chunk, Chunk **chunks, int pos[9][3], int ox, int oy, int oz, int place,  float *outSunStrength)
{
    // outSunStrength는 false를 리턴할 때에만 라이팅에 쓰기 위해 쓴다.
    // 음 이걸... 면단위로 해야겠다. 그리고 어두움 정도는 constant로 한다.
    // 또한........ OpenGL라이팅을 끄고 다 수동으로 하는 건 어떨까?
    // 면단위로 최대 9x9까지 읽어와서
    // 내 바로 위에 있는 건 윗면만 건드리고
    // 아랫면은 항상 어둡게
    // 나머지 4면이 중요한데
    // 123
    // 456 여기서 4번 면이면 1,4,7만 읽어와서 그것만 4번면에 영향을 미친다.
    // 789
    // 1,4,7은 3x3이니까 이걸 9x9로 하면 꽤 그럴듯 함
    //
    // 음......
    //
    // OpenGL라이팅을 끄고 수동으로 하면 태양광의 방향성 그림자도 구현할 수 있음.
    // 단지, 지하에서도 태양광의 방향성이...;;;;
    // 이럴 때는, 9x9를 읽어와서 9x9가 전부 막혀있다면 태양광의 영향을 전혀 받지 않도록 한다.
    // 한개라도 뚫려있다면 뚫려있는 쪽의 면은 태양광의 영향을 받는다.
    //
    // 아. 글구 나중에 radiosity쓰자. ㅋㅋㅋ 결국 라잇맵....
    // 라잇맵과 비슷한데 다른점은 광원이 주변 일정 거리 안의 다른 면이라는 점이다.
    //
    // 아 근데 주변 폴리곤을 읽어오려면...-_-;
    // quads의 점 하나만 읽으면 주변인지 아닌지 알 수 있다.
    // 평균 4000번 루프 도니까
    // 4000*4000번...ㅡㅡ;; 졸라 느리겠네.........
    // 아 그럼 quads도...
    // 청크별로 나눠서
    // 청크별로 하면 되겠구만 뭐... 메모리 필요할 때마다 그때그때 alloc해주나?..
    // 청크 하나당 6메가를 할당하느냐 아니면 뭐..........
    // 6메가 별거 아니자나?
    // 컬러 coord는 float일 필요가 전혀 없다. 255까진데 그냥 char면 된다. colorBuffer도 고친다.
    // 
    //
    // 뭐 일단 다른건 다 접어두고 일단 한 면에 대한 검사부터 하자.
    //
    // 아... 주변 청크 값을 안얻어오니까는 그 청크의 면은 어둡게 보인다;;
    // 일단 주변 청크값 얻어오는 거부터 GenQuads에서 고치자.
    //
    //
    //
    // 현재 면쪽이 뚫리면 50%의 광을 주고, 다른면이 다 뚫려있으면 그면숫자 다 뚫리면 나머지 50%를 준다.
    //
    //

    char *heights = chunk->heights;
    int rad = 9;
    char localHeights[rad*rad];
    int i,k;
    int a,c;
    for(i=0;i<rad*rad;++i)
        localHeights[i] = 127;

    int dox,doy,doz;
    int da,db, dc;
    Chunk * curChunk;
    for(k=0; k<rad;++k)
    {
        c = oz+z+k-(int)((rad-1)/2);
        for(i=0;i<rad;++i)
        {
            a = ox+x+i-(int)((rad-1)/2);
            GetLocalCoords(&da,&db,&dc,&dox,&doy,&doz,a,0,c);
            GetChunkByCoord(&curChunk, chunks, pos, da,db,dc,dox,doy,doz);
            if(!curChunk)
                continue;
            localHeights[k*rad+i] = curChunk->heights[dc*128+da];
        }
    }
    int countHigherThanCurrent = 0;
    int curFaceOpen = false;
    // 버텍스 수준으로 어떻게 하나?
    // 안쪽 버텍스는 그대로 바깥쪽 버텍스는.....
    // 음 이걸 얻어올 때 주변 8개의 sunstr을 다 얻어와서 평균값을 써야한다.
    for(k=0;k<rad;++k)
    {
        for(i=0;i<rad;++i)
        {
            if(localHeights[k*rad+i] > y && DirectionCheck(place, i,k))
            {
                countHigherThanCurrent += 1;
            }
            else
            {
                if(place == 2 && k == 4 && i == 3)
                {
                    curFaceOpen = true;
                }
                else if(place == 3 && k == 4 && i == 5)
                {
                    curFaceOpen = true;
                }
                else if(place == 4 && i == 4 && k == 3)
                {
                    curFaceOpen = true;
                }
                else if(place == 5 && i == 4 && k == 5)
                {
                    curFaceOpen = true;
                }
            }
        }
    }
    if(countHigherThanCurrent == 0 || y >= heights[z*128+x])
        return true;
    else
    {
        *outSunStrength = SunLit(place, countHigherThanCurrent, curFaceOpen);
    }
    return false;
}

int Check6Side(int x, int y, int z, int ox, int oy, int oz, int pos[9][3], Chunk **chunks)
{
    int i=0;
    int foundCount = 0;
    int nxa[6] = {0,0,-1,1,0,0}, nya[6] = {-1,1,0,0,0,0}, nza[6] = {0,0,0,0,-1,1};

    Chunk *curChunk;
    for(i=0;i<6;++i)
    {
        int xnb = x+nxa[i];
        int ynb = y+nya[i];
        int znb = z+nza[i];
        char block = 0;
        int dox = ox;
        int doy = oy;
        int doz = oz;
        int dxnb = xnb;
        int dynb = ynb;
        int dznb = znb;
        if(0 > (xnb))
        {
            dox -= 128;
            dxnb = xnb + 128;
        }
        else if((xnb) >= 128)
        {
            dox += 128;
            dxnb = xnb - 128;
        }

        if(0 > (znb))
        {
            doz -= 128;
            dznb = znb + 128;
        }
        else if((znb) >= 128)
        {
            doz += 128;
            dznb = znb - 128;
        }
        int xzSize = 128*128;
        GetChunkByCoord(&curChunk, chunks, pos, dxnb, dynb, dznb, dox, doy, doz);
        if(curChunk && dynb >= 0 && dynb < 128)
        {
            block = curChunk->chunk[(dznb)*xzSize+(dynb)*128+(dxnb)];
            if(block != BLOCK_EMPTY && block != BLOCK_GLASS && block != BLOCK_LEAVES && block != BLOCK_WATER && block != BLOCK_CHEST)
                foundCount++;
        }

    }
    if(foundCount == 6)
        return true;
    return false;
}

void GenQuads(float *tV[64], float *tT[64], unsigned char *tC[64], int tIdx[64], int tLen[64], float *nsV[64], float *nsT[64], unsigned char *nsC[64], int nsIdx[64], int nsLen[64], float *aV[64], float *aT[64], unsigned char *aC[64], int aIdx[64], int aLen[64], float *iV[64], float *iT[64], unsigned char *iC[64], int iIdx[64], int iLen[64], Octree *root, Octree *parent, Chunk *chunk, Octree **octrees, Chunk **chunks, int pos[9][3], int depth, double frustum[6][4], int x, int y, int z, int ox, int oy, int oz, float vx, float vy, float vz, int lx, int ly, int lz, int updateCoords[64*3], int drawIdx, float sunx, float suny, float sunz)
{
    // 일단 레벨 2까지는 검사하고 레벨 3이 되면 하위의 몇개의 버텍스가 나올것인가를 검사한다. 2패스로. 그러면 거기서 alloc을 하고
    // 다시 버텍스를 채운다.
    // 한 번 채우면 추가하고 이러는건 이 함수를 부르지 않는다.
    // 즉, 얼록은 여기서 한번만 하며, 이걸 부르기 전에 이미 있다면 free를 해줘야 한다.
    // 10초 간격으로 한 번이라도 업데이트가 된 녀석은 30초에 한번씩 이걸 불러준다? 이걸 부르는 게 아니라....
    // 음..... 레벨3 간격으로 불러야하나?
    // 업데이트 할 레벨3 하나만 가지고 업뎃하는 함수를 만들어서
    // 이 함수에서 그걸 부르게 할까? 아니면 PYrex에서 부르게 하자.
    //
    // 아예 처음인지 아니면 완전 새롭게 만드는건지를 Cython에서 검사해서
    // free할건지 안할건지를 결정하고
    // 레벨3 수준에서 그려야 할 놈이라면 그리고 뭐 이러면 된다.
    // 아예 청크를 로드할 때에도 한번에 한 청크를 다 로드하지 말고 그러면 더 빨라지겠네....
    // 생성할 때만 한번에 다하고 말이지....아 로드도 한번에 그냥 다해도 됨;
    // 렌더링만 고치자.
    // 아 고칠게 많은데 이러면......
    //
    // 그냥 이 함수를 쓰고
    // 레벨3일 경우 몇갠지 검사해서 free/alloc해주고
    // 2패스로라기 보다는 다른 함수를 만들어서
    // 그걸 따라들어가면 되는군아.
    // 아 아님 1패쓰로... 아 그럼 iLen이 있어야하겠다.
    // 모자랄 때마다 이전의 2배로 realloc을 해준다.
    //
    // index값을 만들어서 업뎃할 청크를 표시함
    // 그리고 프러스텀 검사는 더이상 안함

    // 물 뒷면 나오게 고침.
    int stride = 128;
    int nx,ny,nz;
    int filledCount;
    Octree *neighbor;
    int bx[8] = {0,1,0,1,0,1,0,1};
    int by_[8] = {0,0,1,1,0,0,1,1};
    int bz[8] = {0,0,0,0,1,1,1,1}; // 옥트리 레벨 7의 8개 좌표 오프셋
    int nxa[6] = {0,0,-1,1,0,0}, nya[6] = {-1,1,0,0,0,0}, nza[6] = {0,0,0,0,-1,1};// 청크 블럭 레벨의 6면검사용 오프셋
    float nox,noy,noz;
    float vdx,vdy,vdz;
    float len;
    float sizeCube;
    float quadBuffer[4][3];
    float dotted;
    int i,j,k;
    // 2197152
    int xzSize = 128*128;
    int xBx;
    int yBy;
    int zBz;
    int xnb;
    int ynb;
    int znb;
    int xBO;
    int yBO;
    int zBO;
    int dox;
    int doy;
    int doz;
    int dxnb;
    int dynb;
    int dznb;
    float sunstrength[9];


    for(i=0; i < depth; ++i)
    {
        stride /= 2;
    }
    sizeCube = sqrt(stride*stride)*2;
    /*
    vdx = vx - (x+ox);
    vdy = vy - (y+oy);
    vdz = vz - (z+oz);
    len = sqrt(vdx*vdx+vdy*vdy+vdz*vdz);
    vdx /= len;
    vdy /= len;
    vdz /= len;
    */
    Chunk *curChunk;
    if(parent->filled != OT_EMPTY)// && SphereInFrustum((float)(x+ox+stride),(float)(y+oy+stride),(float)(z+oz+stride),sizeCube, frustum) > 0)
    {
        filledCount = 0;

        // 아 근데.... 뷰포인트와 이쪽 면과의 DOT이 0.8 이상일 때에만 filledCount+1을 한다.
        // 윗면

        nx = x;
        ny = y+stride*2;
        nz = z;
        /*
        nox = 0.001
        noy = 1.0
        noz = 0.001
        len = cmath.sqrt(nox*nox+noy*noy+noz*noz)
        nox /= len
        noy /= len
        noz /= len
        dotted = nox*vdx+noy*vdy+noz*vdz
        */

        // 아... 이런식으로 하게 되면
        // 현재 청크 속에 4x4속에 카메라가 있는데 다 막혀있으면
        // 현재 청크가 안그려진다.
        // 만약 현재 청크 속에 카메라가 있는지를 검사하던지
        // 현재 청크 자체가 비어있다면 그려야 한다.
        if(0 <= nx && nx < 128 && 0 <= ny  && ny < 128 && 0 <= nz  && nz < 128)
        {
            neighbor = AccessOctreeWithXYZ(root, nx,ny,nz, depth);
            if(neighbor->filled & OT_FILLED && !(neighbor->filled & OT_PARTTRANSPARENT))
                filledCount += 1;
       //     else if(neighbor->filled & OT_YBLOCK)// && dotted >= 0.8)
        //        filledCount += 1;
        }

        // 아랫면
        nx = x;
        ny = y-stride*2;
        nz = z;
        /*
        nox = 0.001
        noy = -1.0
        noz = 0.001
        len = cmath.sqrt(nox*nox+noy*noy+noz*noz)
        nox /= len
        noy /= len
        noz /= len
        dotted = nox*vdx+noy*vdy+noz*vdz
        */
        if(0 <= nx && nx < 128 && 0 <= ny  && ny < 128 && 0 <= nz  && nz < 128)
        {
            neighbor = AccessOctreeWithXYZ(root, nx,ny,nz, depth);
            if(neighbor->filled & OT_FILLED && !(neighbor->filled & OT_PARTTRANSPARENT))
                filledCount += 1;
      //      else if(neighbor->filled & OT_YBLOCK)// && dotted >= 0.8)
       //         filledCount += 1;
        }
        // 오른면
        nx = x+stride*2;
        ny = y;
        nz = z;
        /*
        nox = 1.001
        noy = 0.001
        noz = 0.001
        len = cmath.sqrt(nox*nox+noy*noy+noz*noz)
        nox /= len
        noy /= len
        noz /= len
        dotted = nox*vdx+noy*vdy+noz*vdz
        */

        if(0 <= nx && nx < 128 && 0 <= ny  && ny < 128 && 0 <= nz  && nz < 128)
        {
            neighbor = AccessOctreeWithXYZ(root, nx,ny,nz, depth);
            if(neighbor->filled & OT_FILLED && !(neighbor->filled & OT_PARTTRANSPARENT))
                filledCount += 1;
            //else if(neighbor->filled & OT_XBLOCK)// && dotted >= 0.8)
             //   filledCount += 1;
        }
        // 왼
        nx = x-stride*2;
        ny = y;
        nz = z;
        /*
        nox = -1.001
        noy = 0.001
        noz = 0.001
        len = cmath.sqrt(nox*nox+noy*noy+noz*noz)
        nox /= len
        noy /= len
        noz /= len
        dotted = nox*vdx+noy*vdy+noz*vdz
        */
        if(0 <= nx && nx < 128 && 0 <= ny  && ny < 128 && 0 <= nz  && nz < 128)
        {
            neighbor = AccessOctreeWithXYZ(root, nx,ny,nz, depth);
            if(neighbor->filled & OT_FILLED && !(neighbor->filled & OT_PARTTRANSPARENT))
                filledCount += 1;
           // else if(neighbor->filled & OT_XBLOCK)// && dotted >= 0.8)
           //     filledCount += 1;
        }
        // 앞
        nx = x;
        ny = y;
        nz = z+stride*2;
        /*
        nox = 0.001
        noy = 0.001
        noz = 1.001
        len = cmath.sqrt(nox*nox+noy*noy+noz*noz)
        nox /= len
        noy /= len
        noz /= len
        dotted = nox*vdx+noy*vdy+noz*vdz
        */

        if(0 <= nx && nx < 128 && 0 <= ny  && ny < 128 && 0 <= nz  && nz < 128)
        {
            neighbor = AccessOctreeWithXYZ(root, nx,ny,nz, depth);
            if(neighbor->filled & OT_FILLED && !(neighbor->filled & OT_PARTTRANSPARENT))
                filledCount += 1;
//            else if(neighbor->filled & OT_ZBLOCK)// && dotted >= 0.8)
 //               filledCount += 1;
        }

        // 뒤
        nx = x;
        ny = y;
        nz = z-stride*2;
        /*
        nox = 0.001
        noy = 0.001
        noz = -1.001
        len = cmath.sqrt(nox*nox+noy*noy+noz*noz)
        nox /= len
        noy /= len
        noz /= len
        dotted = nox*vdx+noy*vdy+noz*vdz
        */
        if(0 <= nx && nx < 128 && 0 <= ny  && ny < 128 && 0 <= nz  && nz < 128)
        {
            neighbor = AccessOctreeWithXYZ(root, nx,ny,nz, depth);
            if(neighbor->filled & OT_FILLED && !(neighbor->filled & OT_PARTTRANSPARENT))
                filledCount += 1;
  //          else if(neighbor->filled & OT_ZBLOCK)// && dotted >= 0.8)
   //             filledCount += 1;
        }
        if(filledCount == 6 && parent->filled & OT_FILLED)
        {
            /*
            for(i=0; i<8;++i)
            {
                xBx = x+bx[i];
                yBy = y+by_[i];
                zBz = z+bz[i];
                xBO = xBx+ox;
                yBO = yBy+oy;
                zBO = zBz+oz;
                for(j=0;j<6;++j)
                {
                    xnb = xBx+nxa[j]; // neighbor block coord
                    ynb = yBy+nya[j];
                    znb = zBz+nza[j];

                    if(xnb+ox == lx && ynb+oy == ly && znb+oz == lz)
                    {
                        // 안보이는 블럭은 역시 여기까지 와야하는데 여기까지 안온다.
                        // 프러스텀 컬링에서 걸리나?
                        // 잡았다. 여기서 걸린다. -_-
                        // 으아..........
                        // 여기서 걸린다는 건 뭘 의미하는가. Octree가 제대로 안된다는 의미다.
                        printf("%d front, %d chunk\n", IsPolyFront(j, (xBO), (yBO), (zBO),vx,vy,vz), chunk->chunk[(znb)*xzSize+(ynb)*128+(xnb)]);
                    }
                }
            }
            */

            return;
        }
        //print filledCount

        unsigned char block = 0;
        // 아 이제 여기서 drawIdx에 넣도록 하자.
        if(depth == 5)
        {
            Extra *extra = (Extra*)parent->extra;
            int face;
            float tx,ty,tz;
            float xx,yy,zz,ww,hh;
            // 옥트리와 하잇필드를 저장할 때 토치도 저장한다.
            // 주변에 떨어진 아이템도 그렇게 저장을?
            if(drawIdx != -1)
            {
                for(i=0;i<extra->chestIdx;++i)
                {
                    if(iLen[drawIdx] == 0)
                    {
                        iV[drawIdx] = (float*)malloc(sizeof(float)*3*4*6);
                        iT[drawIdx] = (float*)malloc(sizeof(float)*2*4*6);
                        iC[drawIdx] = (unsigned char*)malloc(sizeof(unsigned char)*3*4*6);
                        iLen[drawIdx] = 6;
                    }
                    if(iLen[drawIdx] <= iIdx[drawIdx]+6)
                    {
                        iV[drawIdx] = (float*)realloc(iV[drawIdx], sizeof(float)*4*3*iLen[drawIdx]*2);
                        iT[drawIdx] = (float*)realloc(iT[drawIdx], sizeof(float)*4*2*iLen[drawIdx]*2);
                        iC[drawIdx] = (unsigned char*)realloc(iC[drawIdx], sizeof(unsigned char)*4*3*iLen[drawIdx]*2);
                        iLen[drawIdx] = iLen[drawIdx]*2;
                    }
                    float *itemquads = &iV[drawIdx][iIdx[drawIdx]*4*3];
                    float *itemtexs = &iT[drawIdx][iIdx[drawIdx]*4*2];
                    unsigned char *itemcolors = &iC[drawIdx][iIdx[drawIdx]*4*3];
                    iIdx[drawIdx] += 6;
                    tx = (float)extra->chests[i].x;
                    ty = (float)extra->chests[i].y;
                    tz = (float)extra->chests[i].z;
                    face = extra->chests[i].frontFacing;
                    xx = tx;
                    yy = ty;
                    zz = tz;
                    ww = 1.0f;
                    hh = 1.0f;

                    itemquads[0] = xx;
                    itemquads[1] = yy;
                    itemquads[2] = zz;
                    itemquads[3] = xx+ww;
                    itemquads[4] = yy;
                    itemquads[5] = zz;
                    itemquads[6] = xx+ww;
                    itemquads[7] = yy;
                    itemquads[8] = zz+ww;
                    itemquads[9] = xx;
                    itemquads[10] = yy;
                    itemquads[11] = zz+ww;
                    //아랫면

                    int iii = 12;
                    itemquads[iii+0] = xx;
                    itemquads[iii+1] = yy+hh;
                    itemquads[iii+2] = zz;
                    itemquads[iii+3] = xx;
                    itemquads[iii+4] = yy+hh;
                    itemquads[iii+5] = zz+ww;
                    itemquads[iii+6] = xx+ww;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz+ww;
                    itemquads[iii+9] = xx+ww;
                    itemquads[iii+10] = yy+hh;
                    itemquads[iii+11] = zz;
                    //윗면

                    iii += 12;
                    itemquads[iii+0] = xx;
                    itemquads[iii+1] = yy;
                    itemquads[iii+2] = zz;

                    itemquads[iii+3] = xx;
                    itemquads[iii+4] = yy;
                    itemquads[iii+5] = zz+ww;

                    itemquads[iii+6] = xx;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz+ww;

                    itemquads[iii+9] = xx;
                    itemquads[iii+10] = yy+hh;
                    itemquads[iii+11] = zz;
                    //왼쪽면

                    iii += 12;
                    itemquads[iii+0] = xx+ww;
                    itemquads[iii+1] = yy;
                    itemquads[iii+2] = zz;

                    itemquads[iii+3] = xx+ww;
                    itemquads[iii+4] = yy+hh;
                    itemquads[iii+5] = zz;

                    itemquads[iii+6] = xx+ww;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz+ww;

                    itemquads[iii+9] = xx+ww;
                    itemquads[iii+10] = yy;
                    itemquads[iii+11] = zz+ww;
                    //오른쪽면

                    iii += 12;
                    itemquads[iii+0] = xx;
                    itemquads[iii+1] = yy;
                    itemquads[iii+2] = zz;

                    itemquads[iii+3] = xx;
                    itemquads[iii+4] = yy+hh;
                    itemquads[iii+5] = zz;

                    itemquads[iii+6] = xx+ww;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz;

                    itemquads[iii+9] = xx+ww;
                    itemquads[iii+10] = yy;
                    itemquads[iii+11] = zz;
                    //뒷면

                    iii += 12;
                    itemquads[iii+0] = xx;
                    itemquads[iii+1] = yy;
                    itemquads[iii+2] = zz+ww;

                    itemquads[iii+3] = xx+ww;
                    itemquads[iii+4] = yy;
                    itemquads[iii+5] = zz+ww;

                    itemquads[iii+6] = xx+ww;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz+ww;

                    itemquads[iii+9] = xx;
                    itemquads[iii+10] = yy+hh;
                    itemquads[iii+11] = zz+ww;
                    //앞면

                    for(iii=0;iii<6;++iii)
                    {
                        float texfrontx = 3*30.0f/512.0f; // 옆면
                        float texfronty = 5*30.0f/512.0f;
                        float texsidex = 3*30.0f/512.0f; // 옆면
                        float texsidey = 6*30.0f/512.0f;
                        float texbackx = 3*30.0f/512.0f; // 옆면
                        float texbacky = 7*30.0f/512.0f;
                        float texupx = 3*30.0f/512.0f; // 윗면
                        float texupy = 2*30.0f/512.0f;
                        float texbotx = 3*30.0f/512.0f; // 아랫면
                        float texboty = 2*30.0f/512.0f;
                        float orgx,offx,orgy,offy;

                        if(iii == 1) { // 윗면, 위에서 봤을 때 반시계방향으로 그린다.
                            orgx = texupx;
                            offx = texupx+(30.0f/512.0f);
                            offy = texupy;
                            orgy = texupy+(30.0f/512.0f);
                            itemtexs[iii*8+0*2+0] = (float)orgx; // 왼뒤
                            itemtexs[iii*8+0*2+1] = (float)offy;

                            itemtexs[iii*8+1*2+0] = (float)orgx; // 왼앞
                            itemtexs[iii*8+1*2+1] = (float)orgy;

                            itemtexs[iii*8+2*2+0] = (float)offx; // 오앞
                            itemtexs[iii*8+2*2+1] = (float)orgy;

                            itemtexs[iii*8+3*2+0] = (float)offx; // 오뒤
                            itemtexs[iii*8+3*2+1] = (float)offy;
                        }
                        else if(iii == 0) { // 아랫면, 아래에서 봤을 때 반시계방향으로 그린다.
                            orgx = texbotx;
                            offx = texbotx+(30.0f/512.0f);
                            offy = texboty;
                            orgy = texboty+(30.0f/512.0f);
                            itemtexs[iii*8+0*2+0] = (float)orgx; // 왼뒤
                            itemtexs[iii*8+0*2+1] = (float)orgy;

                            itemtexs[iii*8+1*2+0] = (float)offx; // 오뒤
                            itemtexs[iii*8+1*2+1] = (float)orgy;

                            itemtexs[iii*8+2*2+0] = (float)offx; // 오앞
                            itemtexs[iii*8+2*2+1] = (float)offy;

                            itemtexs[iii*8+3*2+0] = (float)orgx; // 왼앞
                            itemtexs[iii*8+3*2+1] = (float)offy;
                        }
                        else if(iii == 2) { // 왼쪽면, 왼쪽에서 봤을 때 반시계방향으로 그린다.
                            if(face == 2) // 앞면
                            {
                                orgx = texfrontx;
                                offx = texfrontx+(30.0f/512.0f);
                                offy = texfronty;
                                orgy = texfronty+(30.0f/512.0f);
                            }
                            else if(face == 3) // 뒷면
                            {
                                orgx = texbackx;
                                offx = texbackx+(30.0f/512.0f);
                                offy = texbacky;
                                orgy = texbacky+(30.0f/512.0f);
                            }
                            else
                            {
                                orgx = texsidex;
                                offx = texsidex+(30.0f/512.0f);
                                offy = texsidey;
                                orgy = texsidey+(30.0f/512.0f);
                            }
                            itemtexs[iii*8+0*2+0] = (float)orgx; // 아뒤
                            itemtexs[iii*8+0*2+1] = (float)orgy; //

                            itemtexs[iii*8+1*2+0] = (float)offx; // 아앞
                            itemtexs[iii*8+1*2+1] = (float)orgy; //

                            itemtexs[iii*8+2*2+0] = (float)offx; // 위앞
                            itemtexs[iii*8+2*2+1] = (float)offy; //

                            itemtexs[iii*8+3*2+0] = (float)orgx; //
                            itemtexs[iii*8+3*2+1] = (float)offy; //
                        }
                        else if(iii == 3) { // 오른쪽면, 오른쪽에서 봤을 때 반시계방향으로 그린다.
                            if(face == 3) // 앞면
                            {
                                orgx = texfrontx;
                                offx = texfrontx+(30.0f/512.0f);
                                offy = texfronty;
                                orgy = texfronty+(30.0f/512.0f);
                            }
                            else if(face == 2) // 뒷면
                            {
                                orgx = texbackx;
                                offx = texbackx+(30.0f/512.0f);
                                offy = texbacky;
                                orgy = texbacky+(30.0f/512.0f);
                            }
                            else
                            {
                                orgx = texsidex;
                                offx = texsidex+(30.0f/512.0f);
                                offy = texsidey;
                                orgy = texsidey+(30.0f/512.0f);
                            }
                            itemtexs[iii*8+0*2+0] = (float)offx; // 아뒤
                            itemtexs[iii*8+0*2+1] = (float)orgy; //

                            itemtexs[iii*8+1*2+0] = (float)offx; //
                            itemtexs[iii*8+1*2+1] = (float)offy; //

                            itemtexs[iii*8+2*2+0] = (float)orgx; //
                            itemtexs[iii*8+2*2+1] = (float)offy; //

                            itemtexs[iii*8+3*2+0] = (float)orgx;
                            itemtexs[iii*8+3*2+1] = (float)orgy;
                        }
                        else if(iii == 4) { // 뒷면, 뒷쪽에서 봤을 때 반시계방향으로 그린다. 앞에서 봤을 때 시계방향임
                            if(face == 4) // 앞면
                            {
                                orgx = texfrontx;
                                offx = texfrontx+(30.0f/512.0f);
                                offy = texfronty;
                                orgy = texfronty+(30.0f/512.0f);
                            }
                            else if(face == 5) // 뒷면
                            {
                                orgx = texbackx;
                                offx = texbackx+(30.0f/512.0f);
                                offy = texbacky;
                                orgy = texbacky+(30.0f/512.0f);
                            }
                            else
                            {
                                orgx = texsidex;
                                offx = texsidex+(30.0f/512.0f);
                                offy = texsidey;
                                orgy = texsidey+(30.0f/512.0f);
                            }
                            itemtexs[iii*8+0*2+0] = (float)offx; //
                            itemtexs[iii*8+0*2+1] = (float)orgy; //
                            itemtexs[iii*8+1*2+0] = (float)offx; //
                            itemtexs[iii*8+1*2+1] = (float)offy; //
                            itemtexs[iii*8+2*2+0] = (float)orgx; // 왼위
                            itemtexs[iii*8+2*2+1] = (float)offy; //
                            itemtexs[iii*8+3*2+0] = (float)orgx; // 왼아래
                            itemtexs[iii*8+3*2+1] = (float)orgy;



                        }
                        else if(iii == 5) { // 앞면, 앞쪽에서 봤을 때 반시계방향으로 그린다.
                            if(face == 5) // 앞면
                            {
                                orgx = texfrontx;
                                offx = texfrontx+(30.0f/512.0f);
                                offy = texfronty;
                                orgy = texfronty+(30.0f/512.0f);
                            }
                            else if(face == 4) // 뒷면
                            {
                                orgx = texbackx;
                                offx = texbackx+(30.0f/512.0f);
                                offy = texbacky;
                                orgy = texbacky+(30.0f/512.0f);
                            }
                            else
                            {
                                orgx = texsidex;
                                offx = texsidex+(30.0f/512.0f);
                                offy = texsidey;
                                orgy = texsidey+(30.0f/512.0f);
                            }
                            itemtexs[iii*8+0*2+0] = (float)orgx; // 왼쪽
                            itemtexs[iii*8+0*2+1] = (float)orgy; // 아래

                            itemtexs[iii*8+1*2+0] = (float)offx; //
                            itemtexs[iii*8+1*2+1] = (float)orgy; //

                            itemtexs[iii*8+2*2+0] = (float)offx; //
                            itemtexs[iii*8+2*2+1] = (float)offy; //

                            itemtexs[iii*8+3*2+0] = (float)orgx; //
                            itemtexs[iii*8+3*2+1] = (float)offy; //
                        }
                    }

                    for(iii=0;iii<12*6;++iii)
                    {
                        itemcolors[iii] = 255;
                    }
                }


                for(i=0;i<extra->torchIdx;++i)
                {
                    if(iLen[drawIdx] == 0)
                    {
                        iV[drawIdx] = (float*)malloc(sizeof(float)*3*4*6);
                        iT[drawIdx] = (float*)malloc(sizeof(float)*2*4*6);
                        iC[drawIdx] = (unsigned char*)malloc(sizeof(unsigned char)*3*4*6);
                        iLen[drawIdx] = 6;
                    }
                    if(iLen[drawIdx] <= iIdx[drawIdx]+6)
                    {
                        iV[drawIdx] = (float*)realloc(iV[drawIdx], sizeof(float)*4*3*iLen[drawIdx]*2);
                        iT[drawIdx] = (float*)realloc(iT[drawIdx], sizeof(float)*4*2*iLen[drawIdx]*2);
                        iC[drawIdx] = (unsigned char*)realloc(iC[drawIdx], sizeof(unsigned char)*4*3*iLen[drawIdx]*2);
                        iLen[drawIdx] = iLen[drawIdx]*2;
                    }
                    float *itemquads = &iV[drawIdx][iIdx[drawIdx]*4*3];
                    float *itemtexs = &iT[drawIdx][iIdx[drawIdx]*4*2];
                    unsigned char *itemcolors = &iC[drawIdx][iIdx[drawIdx]*4*3];
                    iIdx[drawIdx] += 6;
                    tx = (float)extra->torches[i].x;
                    ty = (float)extra->torches[i].y;
                    tz = (float)extra->torches[i].z;
                    face = extra->torches[i].face;
                    if(face == 1)
                    {
                        tx += (1.0f-0.15f)/2.0f;
                        ty += 1.0f;
                        tz += (1.0f-0.15f)/2.0f;
                    }
                    else if(face == 2)
                    {
                        tx -= 0.15f;
                        ty += (1.0f-0.6f)/2.0f;
                        tz += (1.0f-0.15f)/2.0f;
                    }
                    else if(face == 3)
                    {
                        tx += 1.0f;
                        ty += (1.0f-0.6f)/2.0f;
                        tz += (1.0f-0.15f)/2.0f;
                    }
                    else if(face == 4)
                    {
                        tx += (1.0f-0.15f)/2.0f;
                        ty += (1.0f-0.6f)/2.0f;
                        tz -= 0.15f;
                    }
                    else if(face == 5)
                    {
                        tx += (1.0f-0.15f)/2.0f;
                        ty += (1.0f-0.6f)/2.0f;
                        tz += 1.0f;
                    }
                    xx = tx;
                    yy = ty;
                    zz = tz;
                    ww = 0.15f;
                    hh = 0.6f;

                    itemquads[0] = xx;
                    itemquads[1] = yy;
                    itemquads[2] = zz;
                    itemquads[3] = xx+ww;
                    itemquads[4] = yy;
                    itemquads[5] = zz;
                    itemquads[6] = xx+ww;
                    itemquads[7] = yy;
                    itemquads[8] = zz+ww;
                    itemquads[9] = xx;
                    itemquads[10] = yy;
                    itemquads[11] = zz+ww;
                    //아랫면

                    int iii = 12;
                    itemquads[iii+0] = xx;
                    itemquads[iii+1] = yy+hh;
                    itemquads[iii+2] = zz;
                    itemquads[iii+3] = xx;
                    itemquads[iii+4] = yy+hh;
                    itemquads[iii+5] = zz+ww;
                    itemquads[iii+6] = xx+ww;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz+ww;
                    itemquads[iii+9] = xx+ww;
                    itemquads[iii+10] = yy+hh;
                    itemquads[iii+11] = zz;
                    //윗면

                    iii += 12;
                    itemquads[iii+0] = xx;
                    itemquads[iii+1] = yy;
                    itemquads[iii+2] = zz;

                    itemquads[iii+3] = xx;
                    itemquads[iii+4] = yy;
                    itemquads[iii+5] = zz+ww;

                    itemquads[iii+6] = xx;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz+ww;

                    itemquads[iii+9] = xx;
                    itemquads[iii+10] = yy+hh;
                    itemquads[iii+11] = zz;
                    //왼쪽면

                    iii += 12;
                    itemquads[iii+0] = xx+ww;
                    itemquads[iii+1] = yy;
                    itemquads[iii+2] = zz;

                    itemquads[iii+3] = xx+ww;
                    itemquads[iii+4] = yy+hh;
                    itemquads[iii+5] = zz;

                    itemquads[iii+6] = xx+ww;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz+ww;

                    itemquads[iii+9] = xx+ww;
                    itemquads[iii+10] = yy;
                    itemquads[iii+11] = zz+ww;
                    //오른쪽면

                    iii += 12;
                    itemquads[iii+0] = xx;
                    itemquads[iii+1] = yy;
                    itemquads[iii+2] = zz;

                    itemquads[iii+3] = xx;
                    itemquads[iii+4] = yy+hh;
                    itemquads[iii+5] = zz;

                    itemquads[iii+6] = xx+ww;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz;

                    itemquads[iii+9] = xx+ww;
                    itemquads[iii+10] = yy;
                    itemquads[iii+11] = zz;
                    //뒷면

                    iii += 12;
                    itemquads[iii+0] = xx;
                    itemquads[iii+1] = yy;
                    itemquads[iii+2] = zz+ww;

                    itemquads[iii+3] = xx+ww;
                    itemquads[iii+4] = yy;
                    itemquads[iii+5] = zz+ww;

                    itemquads[iii+6] = xx+ww;
                    itemquads[iii+7] = yy+hh;
                    itemquads[iii+8] = zz+ww;

                    itemquads[iii+9] = xx;
                    itemquads[iii+10] = yy+hh;
                    itemquads[iii+11] = zz+ww;
                    //앞면

                    for(iii=0;iii<6;++iii)
                    {
                        float texmidx = 3*30.0f/512.0f; // 옆면
                        float texmidy = 0*30.0f/512.0f;
                        float texupx = 3*30.0f/512.0f; // 윗면
                        float texupy = 1*30.0f/512.0f;
                        float texbotx = 3*30.0f/512.0f; // 아랫면
                        float texboty = 2*30.0f/512.0f;
                        float orgx,offx,orgy,offy;

                        if(iii == 1) { // 윗면, 위에서 봤을 때 반시계방향으로 그린다.
                            orgx = texupx;
                            offx = texupx+(30.0f/512.0f);
                            offy = texupy;
                            orgy = texupy+(30.0f/512.0f);
                            itemtexs[iii*8+0*2+0] = (float)orgx; // 왼뒤
                            itemtexs[iii*8+0*2+1] = (float)offy;

                            itemtexs[iii*8+1*2+0] = (float)orgx; // 왼앞
                            itemtexs[iii*8+1*2+1] = (float)orgy;

                            itemtexs[iii*8+2*2+0] = (float)offx; // 오앞
                            itemtexs[iii*8+2*2+1] = (float)orgy;

                            itemtexs[iii*8+3*2+0] = (float)offx; // 오뒤
                            itemtexs[iii*8+3*2+1] = (float)offy;
                        }
                        else if(iii == 0) { // 아랫면, 아래에서 봤을 때 반시계방향으로 그린다.
                            orgx = texbotx;
                            offx = texbotx+(30.0f/512.0f);
                            offy = texboty;
                            orgy = texboty+(30.0f/512.0f);
                            itemtexs[iii*8+0*2+0] = (float)orgx; // 왼뒤
                            itemtexs[iii*8+0*2+1] = (float)orgy;

                            itemtexs[iii*8+1*2+0] = (float)offx; // 오뒤
                            itemtexs[iii*8+1*2+1] = (float)orgy;

                            itemtexs[iii*8+2*2+0] = (float)offx; // 오앞
                            itemtexs[iii*8+2*2+1] = (float)offy;

                            itemtexs[iii*8+3*2+0] = (float)orgx; // 왼앞
                            itemtexs[iii*8+3*2+1] = (float)offy;
                        }
                        else if(iii == 2) { // 왼쪽면, 왼쪽에서 봤을 때 반시계방향으로 그린다.
                            orgx = texmidx;
                            offx = texmidx+(30.0f/512.0f);
                            offy = texmidy;
                            orgy = texmidy+(30.0f/512.0f);
                            itemtexs[iii*8+0*2+0] = (float)orgx; // 아뒤
                            itemtexs[iii*8+0*2+1] = (float)orgy; //

                            itemtexs[iii*8+1*2+0] = (float)offx; // 아앞
                            itemtexs[iii*8+1*2+1] = (float)orgy; //

                            itemtexs[iii*8+2*2+0] = (float)offx; // 위앞
                            itemtexs[iii*8+2*2+1] = (float)offy; //

                            itemtexs[iii*8+3*2+0] = (float)orgx; //
                            itemtexs[iii*8+3*2+1] = (float)offy; //
                        }
                        else if(iii == 3) { // 오른쪽면, 오른쪽에서 봤을 때 반시계방향으로 그린다.
                            orgx = texmidx;
                            offx = texmidx+(30.0f/512.0f);
                            offy = texmidy;
                            orgy = texmidy+(30.0f/512.0f);
                            itemtexs[iii*8+0*2+0] = (float)offx; // 아뒤
                            itemtexs[iii*8+0*2+1] = (float)orgy; //

                            itemtexs[iii*8+1*2+0] = (float)offx; //
                            itemtexs[iii*8+1*2+1] = (float)offy; //

                            itemtexs[iii*8+2*2+0] = (float)orgx; //
                            itemtexs[iii*8+2*2+1] = (float)offy; //

                            itemtexs[iii*8+3*2+0] = (float)orgx;
                            itemtexs[iii*8+3*2+1] = (float)orgy;
                        }
                        else if(iii == 4) { // 뒷면, 뒷쪽에서 봤을 때 반시계방향으로 그린다. 앞에서 봤을 때 시계방향임
                            orgx = texmidx;
                            offx = texmidx+(30.0f/512.0f);
                            offy = texmidy;
                            orgy = texmidy+(30.0f/512.0f);
                            itemtexs[iii*8+0*2+0] = (float)offx; //
                            itemtexs[iii*8+0*2+1] = (float)orgy; //
                            itemtexs[iii*8+1*2+0] = (float)offx; //
                            itemtexs[iii*8+1*2+1] = (float)offy; //
                            itemtexs[iii*8+2*2+0] = (float)orgx; // 왼위
                            itemtexs[iii*8+2*2+1] = (float)offy; //
                            itemtexs[iii*8+3*2+0] = (float)orgx; // 왼아래
                            itemtexs[iii*8+3*2+1] = (float)orgy;



                        }
                        else if(iii == 5) { // 앞면, 앞쪽에서 봤을 때 반시계방향으로 그린다.
                            orgx = texmidx;
                            offx = texmidx+(30.0f/512.0f);
                            offy = texmidy;
                            orgy = texmidy+(30.0f/512.0f);
                            itemtexs[iii*8+0*2+0] = (float)orgx; // 왼쪽
                            itemtexs[iii*8+0*2+1] = (float)orgy; // 아래

                            itemtexs[iii*8+1*2+0] = (float)offx; //
                            itemtexs[iii*8+1*2+1] = (float)orgy; //

                            itemtexs[iii*8+2*2+0] = (float)offx; //
                            itemtexs[iii*8+2*2+1] = (float)offy; //

                            itemtexs[iii*8+3*2+0] = (float)orgx; //
                            itemtexs[iii*8+3*2+1] = (float)offy; //
                        }
                    }

                    for(iii=0;iii<12*6;++iii)
                    {
                        itemcolors[iii] = 255;
                    }
                }
            }

        }
        if(depth == 7)
        {
            // 현재 옥트리 안에 다음의 좌표들이 존재한다.
            Extra *extras[27];
            int strideTorch = 128;
            for(i=0; i<5-1;++i)
                strideTorch /= 2;
            int tx[3] = {x-strideTorch, x, x+strideTorch};
            int ty[3] = {y-strideTorch, y, y+strideTorch};
            int tz[3] = {z-strideTorch, z, z+strideTorch};
            int ttx,tty,ttz;
            Octree *torchOctree;
            for(k=0;k<3;++k)
            {
                for(j=0;j<3;++j)
                {
                    for(i=0;i<3;++i)
                    {
                        torchOctree = NULL;
                        if(0 <= tx[i] && tx[i] < 128 && 0 <= ty[j] && ty[j] < 128 && 0 <= tz[k] && tz[k] < 128)
                        {
                            torchOctree = AccessOctreeWithXYZ(root, tx[i],ty[j],tz[k], 5);
                        }
                        else
                        {
                            dox = ox;
                            doy = oy;
                            doz = oz;
                            ttx=tx[i];
                            tty=ty[j];
                            ttz=tz[k];
                            if(ttx < 0)
                            {
                                dox -= 128;
                                ttx += 128;
                            }
                            else if(ttx >= 128)
                            {
                                dox += 128;
                                ttx -= 128;
                            }
                            if(ttz < 0)
                            {
                                doz -= 128;
                                ttz += 128;
                            }
                            else if(ttz >= 128)
                            {
                                doz += 128;
                                ttz -= 128;
                            }
                            int ii;
                            for(ii=0;ii<9;++ii)
                            {
                                if(pos[ii][0] == dox && pos[ii][2] == doz)
                                {
                                    torchOctree = AccessOctreeWithXYZ(octrees[ii], ttx,tty,ttz, 6);
                                    break;
                                }
                            }
                        }
                        if(torchOctree)
                            extras[k*3*3+j*3+i] = (Extra*)torchOctree->extra;
                        else
                            extras[k*3*3+j*3+i] = (Extra*)NULL;
                    }
                }
            }
    //cdef Octree * AccessOctreeWithXYZ(self, Octree * root, int x, int y, int z, int targetdepth, int *newx, int *newy, int *newz):
      //  return self.AccessRecur(root, 0,0,0,x,y,z,1, targetdepth, newx, newy, newz)
                                    //neighbor =  이걸로 토치를 가져온다.

            for(i=0; i<8;++i)
            {
                xBx = x+bx[i];
                yBy = y+by_[i];
                zBz = z+bz[i];
                xBO = xBx+ox;
                yBO = yBy+oy;
                zBO = zBz+oz;
                char curBlock = chunk->chunk[(zBz)*xzSize+(yBy)*128+(xBx)];
                if(curBlock != 0) // 만약 현재 블럭이 empty가 아니라면
                {
                    for(j=0;j<6;++j)
                    {
                        xnb = xBx+nxa[j]; // neighbor block coord
                        ynb = yBy+nya[j];
                        znb = zBz+nza[j];
                        if(0 <= (xnb) && (xnb) < 128 && 0 <= (ynb) && (ynb) < 128 && 0 <= (znb) && (znb) < 128)
                        {
                            block = chunk->chunk[(znb)*xzSize+(ynb)*128+(xnb)];
                        }
                        else
                        {
                            block = 0;
                            dox = ox;
                            doy = oy;
                            doz = oz;
                            dxnb = xnb;
                            dynb = ynb;
                            dznb = znb;
                            if(0 > (xnb))
                            {
                                dox -= 128;
                                dxnb = xnb + 128;
                            }
                            else if((xnb) >= 128)
                            {
                                dox += 128;
                                dxnb = xnb - 128;
                            }

                            if(0 > (znb))
                            {
                                doz -= 128;
                                dznb = znb + 128;
                            }
                            else if((znb) >= 128)
                            {
                                doz += 128;
                                dznb = znb - 128;
                            }
                            GetChunkByCoord(&curChunk, chunks, pos, dxnb, dynb, dznb, dox, doy, doz);
                            if(curChunk && dynb >= 0 && dynb < 128)
                            {
                                block = curChunk->chunk[(dznb)*xzSize+(dynb)*128+(dxnb)];
                            }

                        }
                        if(block == BLOCK_EMPTY || block == BLOCK_LEAVES || block == BLOCK_CHEST || (block == BLOCK_WATER && curBlock != BLOCK_WATER) || (block == BLOCK_GLASS && curBlock != BLOCK_GLASS))// 만약 현재 옆블럭이 빈 블럭이거나 물/유리라면, 이거 왜 잘 안되지? 시야에따라서 잘 보이기도 하고 안보이기도 한다. OpenGL의 문제인가? 아 알파.
                        // 아. 아무래도. 폭포와 물을 분리하고, 물은 가장 높은곳에 있는 물의 버퍼를 만들어서 가장 높은곳에 있는 물만
                        // 렌더링하게 하고, 폭포는 아무데나 렌더링하고
                        // 유리는 6면으로는 절대 겹쳐지지 않도록 만들고
                        // 이래야겠다.
                        // 블럭을 modify할 때 6면에 물이 있으면 그 물은 폭포수로 바꾸어 버린다.?
                        // 즉, 가장 높은곳에 있는 물이 아닌데 그 물이 보여야하는 경우가 있다. 꼭 폭포수로 안바꿔도 "보이는 물"과 안보일 수 있는 물을 분리한다.
                        // 보이는 물이 점점 많아질수록 느려지겠지. 그렇다면 보이는 물이 퍼지는 경우 그 물이 안보이는 물이 되어버릴 때 보통물로 바꾼다.
                        // XX: 유리나 물의 6면이 모두 다 EMPTY가 아니라면 절대 그리지 않는다.
                        // 음 그려지는 건 근데 유리나 물이 아니라 그 주변인데..;;;
                        // 그렇다면 주변에 있는 블럭에 대한 6면 역시 검사해야 하나? 으아...느리겠구먼.
                        // 물이나 유리일때만 검사하면 된다.
                        {
                            if((block == BLOCK_WATER && curBlock != BLOCK_WATER) || (block == BLOCK_LEAVES && curBlock != BLOCK_LEAVES) || (block == BLOCK_GLASS && curBlock != BLOCK_GLASS))
                            {
                                if(Check6Side(xnb, ynb, znb, ox, oy, oz, pos, chunks))
                                    continue;
                            }

                            
                            // j값에 따라 위,오른쪽,앞면의 블럭을 가져와야할 수도 있으니 고친다
                            if(chunk->colors[(zBz)*xzSize*3+(yBy)*128*3+(xBx*3)])
                                ;

                            int ttt;
                            for(ttt=0; ttt<9;++ttt)
                            {
                                sunstrength[ttt] = 1.0f; // 이거 8방향만 하는게 아니라 26방향으로 해야 제대로 된다. XXX
                                //XXX 또한 FillColor에서 토치와 현재 버텍스 사이에 블럭이 하나라도 있으면 빛을 받지 않도록 한다.
                                //주변에 받는 빛이 반사되어 여기에 받을 수 있음.
                                //이거만 잘해도 radiosity같은거 없이 멋진 라이팅 가능하다.
                                //음...근데 느린데? 컬러 캐슁을 구현해야겠다. 블럭이 변경될 때에만 컬러를 바꾸는거.
                                //블럭변경, 토치변경 등등에서 한다.
                                //그리고 태양의 위치에 따라 빛의 방향도 바꿔줘야 한다.
                                //전부 다 TODO...
                                //일단 캐슁 먼저 그리고 26방향 먼저 구현함.
                                //청크 하나당 약 12메가 정도 먹는다. 별것 아닌거같은데
                                //아 아니지. 6면을 다 가질 필요 없이 3면만 가지면 되지 않나?
                                //노멀을 쓰면 6면 다 필요함. 근데 밑면은 아래면의 윗면이고.....
                                //그렇다면 음......x=0,y=0,z=0의 3면만 하도록 하자. 중요한 건, block이 BLOCK_EMPTY일 때에도 컬러를 가지는 것.
                                //만약 컬러버퍼의 값이 0이라면 채우고, 최소값은 무조건 1이 되도록 하면 된다.
                            }

                            if(TestSunLit(xBx, yBy, zBz, chunk, chunks, pos, ox, oy, oz, 1, &sunstrength[0]))
                            {
                                //sunstrength
                                //여기서 노멀과 태양위치로 쉐이딩
                            }

                            Chunk *curLitChunk=NULL;
                            int a,b,c,A,B,C;

                            GetLocalCoords(&a,&b,&c,&A,&B,&C,xBO-1,yBO,zBO-1);
                            GetChunkByCoord(&curLitChunk, chunks, pos, a,b,c,A,B,C);
                            if(curLitChunk)
                            {
                                TestSunLit(a, b, c, curLitChunk, chunks, pos, A, B, C, 1, &sunstrength[1]);
                            }
                            GetLocalCoords(&a,&b,&c,&A,&B,&C,xBO,yBO,zBO-1);
                            GetChunkByCoord(&curLitChunk, chunks, pos, a,b,c,A,B,C);
                            if(curLitChunk)
                            {
                                TestSunLit(a, b, c, curLitChunk, chunks, pos, A, B, C, 1, &sunstrength[2]);
                            }
                            GetLocalCoords(&a,&b,&c,&A,&B,&C,xBO+1,yBO,zBO-1);
                            GetChunkByCoord(&curLitChunk, chunks, pos, a,b,c,A,B,C);
                            if(curLitChunk)
                            {
                                TestSunLit(a, b, c, curLitChunk, chunks, pos, A, B, C, 1, &sunstrength[3]);
                            }
                            GetLocalCoords(&a,&b,&c,&A,&B,&C,xBO-1,yBO,zBO);
                            GetChunkByCoord(&curLitChunk, chunks, pos, a,b,c,A,B,C);
                            if(curLitChunk)
                            {
                                TestSunLit(a, b, c, curLitChunk, chunks, pos, A, B, C, 1, &sunstrength[4]);
                            }
                            GetLocalCoords(&a,&b,&c,&A,&B,&C,xBO+1,yBO,zBO);
                            GetChunkByCoord(&curLitChunk, chunks, pos, a,b,c,A,B,C);
                            if(curLitChunk)
                            {
                                TestSunLit(a, b, c, curLitChunk, chunks, pos, A, B, C, 1, &sunstrength[5]);
                            }
                            GetLocalCoords(&a,&b,&c,&A,&B,&C,xBO-1,yBO,zBO+1);
                            GetChunkByCoord(&curLitChunk, chunks, pos, a,b,c,A,B,C);
                            if(curLitChunk)
                            {
                                TestSunLit(a, b, c, curLitChunk, chunks, pos, A, B, C, 1, &sunstrength[6]);
                            }
                            GetLocalCoords(&a,&b,&c,&A,&B,&C,xBO,yBO,zBO+1);
                            GetChunkByCoord(&curLitChunk, chunks, pos, a,b,c,A,B,C);
                            if(curLitChunk)
                            {
                                TestSunLit(a, b, c, curLitChunk, chunks, pos, A, B, C, 1, &sunstrength[7]);
                            }
                            GetLocalCoords(&a,&b,&c,&A,&B,&C,xBO+1,yBO,zBO+1);
                            GetChunkByCoord(&curLitChunk, chunks, pos, a,b,c,A,B,C);
                            if(curLitChunk)
                            {
                                TestSunLit(a, b, c, curLitChunk, chunks, pos, A, B, C, 1, &sunstrength[8]);
                            }

                            if(curBlock == BLOCK_WATER || curBlock == BLOCK_GLASS || curBlock == BLOCK_LEAVES || curBlock == BLOCK_CHEST)
                            {
                                //if(IsPolyFront(j, (xBO), (yBO), (zBO),vx,vy,vz)) // Front검사도 더이상 하지 않는다.
                                    // 프러스텀컬링 front검사는 할 필요가 없다. 제대로 된OpenGL에서는 이런걸 알아서 한다.
                                    // 매번 이걸 검사하는게 더 느리다. 왜냐면 캐슁을 하기 때문!
                                    // 그래도 하고싶다면 매번 렌더링할 때마다 사각형 리스트 수준에서 프러스텀/압면검사 해주고
                                    // indexed list를 만들어서 렌더링해주면 된다.
                                    // 어차피 폴리곤의 수가 그렇게 많지가 않을거기 때문에.
                                    // 최악의 경우 64*64*64*6*4*3*4바이트 만큼의 버텍스 버퍼가 필요한데
                                    // 그래봤자 75메가 밖에 안된다.
                                    // 폴리곤 6백만개면....좀 많지만 그렇게 맵을 만들놈이 과연 있을까!!!!! 하하하. (.......)
                                    // 최악의 경우란, 지그재그로 블럭을 한칸씩 쌓는걸 말한다.
                                    // 또한 이렇게 하면 바닥 끝까지 다 보이고 G_FAR를 마음대로 멀리 할 수 있다.
                                    // 또한 원래...64아래쪽만 땅이므로 일부러 그렇게 다파고 그런식으로 쌓지 않는 이상 실질적인 최악의 경우는
                                    // 건물을 지은 경우에도 한....
                                    // 50*50*50의 구조물일 경우 속에 지그재그로 하지 않는 이상 표면적인 250*6개의 큐브가 필요하다.
                                    // 그러면 폴리곤이 36000개이다. 대충 한 10만개의 폴리곤이 바로 최악의 경우이다. 별로 안됨..~
                                    // 평균적으로는 대충.... 7만개의 폴리곤이 항상 그려질 것 같고 128*128을 보여주지 않고 욕심내지 않으면
                                    // 그보다 더 적은 폴리곤이 필요하지 않나 싶다. 대충 64*64만 그린다면...2만개의 폴리곤.
                                    // 128*128을 할지 80*80을 할지는 어차피 Cython에서 결정한다.
                                {
                                    if(drawIdx == -1)
                                        printf("error");
                                    if(aLen[drawIdx] == 0)
                                    {
                                        aV[drawIdx] = (float*)malloc(sizeof(float)*3*4);
                                        aT[drawIdx] = (float*)malloc(sizeof(float)*2*4);
                                        aC[drawIdx] = (unsigned char*)malloc(sizeof(unsigned char)*3*4);
                                        aLen[drawIdx] = 1;
                                    }
                                    if(aLen[drawIdx] <= aIdx[drawIdx]+1)
                                    {
                                        aV[drawIdx] = (float*)realloc(aV[drawIdx], sizeof(float)*4*3*aLen[drawIdx]*2);
                                        aT[drawIdx] = (float*)realloc(aT[drawIdx], sizeof(float)*4*2*aLen[drawIdx]*2);
                                        aC[drawIdx] = (unsigned char*)realloc(aC[drawIdx], sizeof(unsigned char)*4*3*aLen[drawIdx]*2);
                                        aLen[drawIdx] = aLen[drawIdx]*2;
                                    }


                                    GenQuad(&aV[drawIdx][aIdx[drawIdx]*12], j, (xBO), (yBO), (zBO));
                                    FillTex(&aT[drawIdx][aIdx[drawIdx]*8], j, chunk->chunk[(zBz)*xzSize+(yBy)*128+(xBx)]);
                                    FillColor((xBO), (yBO), (zBO), j, &aC[drawIdx][aIdx[drawIdx]*12], sunstrength, extras);
                                    aIdx[drawIdx] += 1;
                                }
                            }
                            else// if(IsPolyFront(j, (xBO), (yBO), (zBO),vx,vy,vz)) // 만약 현재 면이 앞면 즉 그려지는 면이라면
                            {
                                // 이제 여기서....
                                // 아 컬러 버퍼가 필요함.
                                // 그래서..여기서 라이팅 torch등으로 계산하고 태양 영향 받는거 검사하고.
                                // 라이팅은 간단하게 현재 블럭과 torch나 lava와의 거리로 컬러를 결정할 뿐!
                                //
                                //
                                // 에러가 있다. 땅밑으로 일정 이상 파게 되면 안그려지는 면들이 많이 있다.
                                // 옆블럭이 빈블럭이 아니라서?
                                // 렌더 리스트에 안들어가는데, 그 이유는 무엇인가? 다고침
                                
                                if(TestSunLit(xBx, yBy, zBz, chunk, chunks, pos, ox, oy, oz, j, &sunstrength[0])) 
                                {
                                    if(drawIdx == -1)
                                        printf("error");
                                    if(tLen[drawIdx] == 0)
                                    {
                                        tV[drawIdx] = (float*)malloc(sizeof(float)*3*4);
                                        tT[drawIdx] = (float*)malloc(sizeof(float)*2*4);
                                        tC[drawIdx] = (unsigned char*)malloc(sizeof(unsigned char)*3*4);
                                        tLen[drawIdx] = 1;
                                    }
                                    if(tLen[drawIdx] <= tIdx[drawIdx]+1)
                                    {
                                        tV[drawIdx] = (float*)realloc(tV[drawIdx], sizeof(float)*4*3*tLen[drawIdx]*2);
                                        tT[drawIdx] = (float*)realloc(tT[drawIdx], sizeof(float)*4*2*tLen[drawIdx]*2);
                                        tC[drawIdx] = (unsigned char*)realloc(tC[drawIdx], sizeof(unsigned char)*4*3*tLen[drawIdx]*2);
                                        tLen[drawIdx] = tLen[drawIdx]*2;
                                    }
                                    TestSunLit(xBx, yBy, zBz, chunk, chunks, pos, ox, oy, oz, j, &sunstrength[0]);
                                    GenQuad(&tV[drawIdx][tIdx[drawIdx]*12], j, (xBO), (yBO), (zBO));
                                    FillTex(&tT[drawIdx][tIdx[drawIdx]*8], j, chunk->chunk[(zBz)*xzSize+(yBy)*128+(xBx)]);
                                    FillColor((xBO), (yBO), (zBO), j, &tC[drawIdx][tIdx[drawIdx]*12], sunstrength, extras);
                                    tIdx[drawIdx] += 1;
                                }
                                else
                                {// 이걸 하면 일정 Y값 이하의 블럭들이 안보인다. 뭔가가 잘못됨~~~~~~~~ 고침
                                    // 새로운 문제. 경계선의 그림자가 엉망. 왤까 - 고침
                                    //
                                    if(drawIdx == -1)
                                        printf("error");
                                    if(nsLen[drawIdx] == 0)
                                    {
                                        nsV[drawIdx] = (float*)malloc(sizeof(float)*3*4);
                                        nsT[drawIdx] = (float*)malloc(sizeof(float)*2*4);
                                        nsC[drawIdx] = (unsigned char*)malloc(sizeof(unsigned char)*3*4);
                                        nsLen[drawIdx] = 1;
                                    }
                                    if(nsLen[drawIdx] <= nsIdx[drawIdx]+1)
                                    {
                                        nsV[drawIdx] = (float*)realloc(nsV[drawIdx], sizeof(float)*4*3*nsLen[drawIdx]*2);
                                        nsT[drawIdx] = (float*)realloc(nsT[drawIdx], sizeof(float)*4*2*nsLen[drawIdx]*2);
                                        nsC[drawIdx] = (unsigned char*)realloc(nsC[drawIdx], sizeof(unsigned char)*4*3*nsLen[drawIdx]*2);
                                        nsLen[drawIdx] = nsLen[drawIdx]*2;
                                    }
                                    GenQuad(&nsV[drawIdx][nsIdx[drawIdx]*12], j, (xBO), (yBO), (zBO));
                                    FillTex(&nsT[drawIdx][nsIdx[drawIdx]*8], j, chunk->chunk[(zBz)*xzSize+(yBy)*128+(xBx)]);
                                    FillColor((xBO), (yBO), (zBO), j, &nsC[drawIdx][nsIdx[drawIdx]*12], sunstrength, extras);
                                    nsIdx[drawIdx] += 1;
                                }
                            }
                        }
                    }
                }
                                // j번째는 무조건 그림
            }                       
            // 모든 6면검사가 끝났으므로 여기서 블럭수준의 6면검사를 하고 quad를 채운다.
            // 48번의 검사를 해야하네?
        }
        else
        {
            // 주변 6개가 다 filled가 아니라면 차일드로 간다
            // 여기서 주변이 다 filled라면 들어갈 필요도 없다. 겉부분, 청크와 청크의 경계면들만 들어가면 된다.

            for(k=0;k<2;++k)
            {
                for(j=0;j<2;++j)
                {
                    for(i=0;i<2;++i)
                    {
                        if(depth == 2) // 뎁쓰가 몇인지 정확하게, i,j,k를 써야하는지 그런걸 본다. 아마 뎁쓰 2로 해야하고 ijk를써야할 것 같다.
                        {
                            int iiii=0;
                            char coordFound = false;
                            for(iiii=0;iiii<64;++iiii)
                            {
                                if(x+ox+i*32 == updateCoords[iiii*3+0] && y+oy+j*32 == updateCoords[iiii*3+1] && z+oz+k*32 == updateCoords[iiii*3+2])
                                {
                                    coordFound = true;
                                    break;
                                }
                            }
                            if(coordFound)
                            {
                                tIdx[iiii] = 0;
                                nsIdx[iiii] = 0;
                                aIdx[iiii] = 0;
                                iIdx[iiii] = 0;

                                GenQuads(tV, tT, tC, tIdx, tLen, nsV, nsT, nsC, nsIdx, nsLen, aV, aT, aC, aIdx, aLen, iV, iT, iC, iIdx, iLen, root, parent->children[k*2*2+j*2+i], chunk, octrees, chunks, pos, depth+1, frustum, x+(i*stride), y+(j*stride), z+(k*stride), ox,oy,oz, vx,vy,vz, lx,ly,lz, updateCoords, iiii,sunx,suny,sunz);
                            }
                        }
                        else
                        {
                            GenQuads(tV, tT, tC, tIdx, tLen, nsV, nsT, nsC, nsIdx, nsLen, aV, aT, aC, aIdx, aLen, iV, iT, iC, iIdx, iLen, root, parent->children[k*2*2+j*2+i], chunk, octrees, chunks, pos, depth+1, frustum, x+(i*stride), y+(j*stride), z+(k*stride), ox,oy,oz, vx,vy,vz, lx,ly,lz, updateCoords, drawIdx,sunx,suny,sunz);
                        }
                    }
                }
            }
        }
    }
}


void GetUpdated(int vx, int vy, int vz, int updateCoords[64*3])
{
    int sightLen = 64;
    int vxMod, vyMod, vzMod;
    if(vx >= 0)
        vxMod = vx%32;
    else
    {
        vxMod = vx;
        while(vxMod < 0)
            vxMod -= 32;
    }
    if(vy >= 0)
        vyMod = vy%32;
    else
    {
        vyMod = vy;
        while(vyMod < 0)
            vyMod -= 32;
    }
    if(vz >= 0)
        vzMod = vz%32;
    else
    {
        vzMod = vz;
        while(vzMod < 0)
            vzMod -= 32;
    }
    int curCX = vx-vxMod-32*2;
    int curCY = vy-vyMod-32*2;
    int curCZ = vz-vzMod-32*2;
    int x,y,z,i,j;
    int curToDrawList[64*3];
    for(z=0;z<4;++z)
    {
        for(y=0;y<4;++y)
        {
            for(x=0;x<4;++x)
            {
                curToDrawList[z*4*4*3+y*4*3+x*3+0] = curCX+32*x;
                curToDrawList[z*4*4*3+y*4*3+x*3+1] = curCY+32*y;
                curToDrawList[z*4*4*3+y*4*3+x*3+2] = curCZ+32*z;
            }
        }
    }

    int matchedCoords[64*3];
    memset(matchedCoords, 0, sizeof(int)*64*3);
    int idx=0;
    for(i=0;i<64;++i)
    {
        for(j=0;j<64;++j)
        {
            if(updateCoords[i*3+0] == curToDrawList[j*3+0] && updateCoords[i*3+1] == curToDrawList[j*3+1] && updateCoords[i*3+2] == curToDrawList[j*3+2])
            {
                matchedCoords[i*3+0] = curToDrawList[j*3+0];
                matchedCoords[i*3+1] = curToDrawList[j*3+1];
                matchedCoords[i*3+2] = curToDrawList[j*3+2];
                idx += 1;
                break;
            }
        }
    }

    if(idx != 64)
    {
        int unmatchedIdx[64];
        int uidx2 = 0;
        for(i=0;i<64;++i)
        {
            char matchFound = false;
            for(j=0;j<64;++j)
            {
                if(updateCoords[i*3+0] == matchedCoords[j*3+0] && updateCoords[i*3+1] == matchedCoords[j*3+1] && updateCoords[i*3+2] == matchedCoords[j*3+2])
                {
                    matchFound = true;
                    break;
                }
            }
            if(matchFound == false)
            {
                unmatchedIdx[uidx2] = i;
                uidx2 += 1;
            }
        }

        int updatedDrawList[64*3];
        int upidx2 = 0;
        for(i=0;i<64;++i)
        {
            char matchFound = false;
            for(j=0;j<64;++j)
            {
                if(curToDrawList[i*3+0] == matchedCoords[j*3+0] && curToDrawList[i*3+1] == matchedCoords[j*3+1] && curToDrawList[i*3+2] == matchedCoords[j*3+2])
                {
                    matchFound = true;
                    break;
                }
            }
            if(matchFound == false)
            {
                updatedDrawList[upidx2*3+0] = curToDrawList[i*3+0];
                updatedDrawList[upidx2*3+1] = curToDrawList[i*3+1];
                updatedDrawList[upidx2*3+2] = curToDrawList[i*3+2];
                upidx2 += 1;
            }
        }

        int upidx3 = 0;
        for(i=0;i<64;++i)
        {
            char matchFound = false;
            for(j=0;j<uidx2;++j)
            {
                if(i == unmatchedIdx[j])
                {
                    matchFound = true;
                    break;
                }
            }
            if(matchFound)
            {
                updateCoords[i*3+0] = updatedDrawList[upidx3*3+0];
                updateCoords[i*3+1] = updatedDrawList[upidx3*3+1];
                updateCoords[i*3+2] = updatedDrawList[upidx3*3+2];
                upidx3++;
            }
        }
    }
}


//벽에 붙어서 이동을 해야하니까 블럭에 겹쳐지면
// X축 또는 Z축쪽을 따라서 이동하는 그런걸 해야겠다.
// 음....바운딩 박스가 크면 그만큼 많은 블럭과 충돌검사를 해야한다.
// 세로 길이가 2라면 세로로 5만큼의 블럭을
// 가로 길이가 1이라면 가로로 3만큼의 블럭을... 등등.
//
// 박스 인터섹션은 쉽다.
// 스피어 인터섹션 필요없고 위치로 무조건 박스로 생각한다.
int InBox(float ox,float oy,float oz, float dx, float dy, float dz, float x, float y, float z)
{
    if(ox <= x && x < dx && oy <= y && y < dy && oz <= z && z < dz)
        return true;
    else
        return false;
}
int BoxBoxCollide(float ox1,float oy1,float oz1,float  dx1,float dy1,float dz1,float  ox2,float oy2,float oz2,float  dx2,float dy2,float dz2)
{
    float x,y,z;
    x=ox2; y=oy2; z= oz2;
    if(InBox(ox1,oy1,oz1,dx1,dy1,dz1,x,y,z))
        return true;
    x=ox2; y=dy2; z= oz2;
    if(InBox(ox1,oy1,oz1,dx1,dy1,dz1,x,y,z))
        return true;
    x=ox2; y=oy2; z= dz2;
    if(InBox(ox1,oy1,oz1,dx1,dy1,dz1,x,y,z))
        return true;
    x=ox2; y=dy2; z= dz2;
    if(InBox(ox1,oy1,oz1,dx1,dy1,dz1,x,y,z))
        return true;

    x=dx2; y=oy2; z= oz2;
    if(InBox(ox1,oy1,oz1,dx1,dy1,dz1,x,y,z))
        return true;
    x=dx2; y=dy2; z= oz2;
    if(InBox(ox1,oy1,oz1,dx1,dy1,dz1,x,y,z))
        return true;
    x=dx2; y=oy2; z= dz2;
    if(InBox(ox1,oy1,oz1,dx1,dy1,dz1,x,y,z))
        return true;
    x=dx2; y=dy2; z= dz2;
    if(InBox(ox1,oy1,oz1,dx1,dy1,dz1,x,y,z))
        return true;

    x=ox1; y=oy1; z= oz1;
    if(InBox(ox2,oy2,oz2,dx2,dy2,dz2,x,y,z))
        return true;
    x=ox1; y=dy1; z= oz1;
    if(InBox(ox2,oy2,oz2,dx2,dy2,dz2,x,y,z))
        return true;
    x=ox1; y=oy1; z= dz1;
    if(InBox(ox2,oy2,oz2,dx2,dy2,dz2,x,y,z))
        return true;
    x=ox1; y=dy1; z= dz1;
    if(InBox(ox2,oy2,oz2,dx2,dy2,dz2,x,y,z))
        return true;

    x=dx1; y=oy1; z= oz1;
    if(InBox(ox2,oy2,oz2,dx2,dy2,dz2,x,y,z))
        return true;
    x=dx1; y=dy1; z= oz1;
    if(InBox(ox2,oy2,oz2,dx2,dy2,dz2,x,y,z))
        return true;
    x=dx1; y=oy1; z= dz1;
    if(InBox(ox2,oy2,oz2,dx2,dy2,dz2,x,y,z))
        return true;
    x=dx1; y=dy1; z= dz1;
    if(InBox(ox2,oy2,oz2,dx2,dy2,dz2,x,y,z))
        return true;
    return false;

}

int CheckWalkable(char block)
{
    if(block == BLOCK_EMPTY || block == BLOCK_WATER || block == BLOCK_LAVA)
    {
        return true;
    }
    else
        return false;
}
int CheckCollide(float x, float y, float z, float vx, float vy, float vz, float bx, float by, float bz, float ydiff)
{
    return BoxBoxCollide(x-0.19f,y-0.19f,z-0.19f,x+1.19f,y+1.19f,z+1.19f,vx-(float)bx/2.0f, vy+0.001, vz-(float)bz/2.0f, vx+(float)bx/2.0f, vy+by-0.001, vz+(float)bz/2.0f);
}
int InWater(float x, float y, float z, float vx, float vy, float vz)
{
    return (InBox(x,y,z,x+1.0,y+1.0,z+1.0,vx,vy,vz));
}

void GenIndexList(unsigned int *outIndexList, int *outIndexLen, float *quads, int quadLen, float vx, float vy, float vz)
{
    int i,j;
    outIndexLen[0] = 0;
    for(i=0;i<quadLen;++i)
    {
        if(IsPolyFront2(&quads[i*4*3], vx,vy,vz))
        {
            outIndexList[outIndexLen[0]] = i*4+0;
            outIndexList[outIndexLen[0]+1] = i*4+1;
            outIndexList[outIndexLen[0]+2] = i*4+2;
            outIndexList[outIndexLen[0]+3] = i*4+3;
            outIndexLen[0] += 4;
        }
    }
}

void FixPos(fx,fy,fz, ox,oy,oz,nx,ny,nz,bx,by,bz, octrees, chunks, pos)
float *fx,*fy,*fz,ox,oy,oz,nx,ny,nz; // OUT fixed pos, original pos, new pos
int bx,by,bz; // bounding boxes
Octree *octrees[9]; // nearby chunks, octrees
Chunk *chunks[9];
// 음............FixPos를 하는 게 아니라, 그냥 collide하는 순간 ox를 리턴한다?
// 그리고 "조금씩" 움직이면 되지 않을까... 아예 그 반복을 여기에 넣는다. 음...길이 몇씩 움직일까?
// 1.0을 10으로 나누어서 하자.
int pos[9][3];
{
    int lenX,lenY,lenZ;
    float hx,hy,hz; // half bx
    hx = (float)bx/2.0f;
    hy = (float)by;
    hz = (float)bz/2.0f;
    float px,py,pz; // prev ox-step->nx
    // bx = 2
    // 3/2=1
    // 1*2+3 = 3
    // bx= 3
    // 4/2=2
    // 2*2+3=7
    lenX = ((bx+1)/2)*2+5;
    lenY = ((by+1)/2)*2+5;
    lenZ = ((bz+1)/2)*2+5;
    unsigned char *nearbyBlocks;
    nearbyBlocks = (unsigned char *)malloc(sizeof(unsigned char)*lenX*lenY*lenZ);
    int i,j,k,ii;
    int a,b,c,A,B,C;
    int x,y,z;
    x = (int)(ox);
    y = (int)(oy);
    z = (int)(oz);
    x -= lenX/2;
    y -= lenY/2;
    z -= lenZ/2;
    int xySize = 128*128;
    unsigned char block;
    float sx,sy,sz;
    float curx,cury,curz;
    sx = ox;
    sy = oy;
    sz = oz;
    float stepx,stepy,stepz;
    int found;
    int step;
    const int steps = 10;
    stepx = (nx-ox)/(float)steps;
    stepy = (ny-oy)/(float)steps;
    stepz = (nz-oz)/(float)steps;
    // 여기서 일단 x쪽이 비었는지 y쪽이 비었는지를 본다.
    // 사다리 올라갈 때에도 대비해야함 XXX:
    int xEmpty, zEmpty, yEmpty;
    xEmpty = true;
    zEmpty = true;
    yEmpty = true;
    Chunk *curChunk;

    if(ox!=nx || oz!=nz)
    {
        GetLocalCoords(&a,&b,&c,&A,&B,&C,(int)ox+1,(int)oy-1,(int)oz);
        GetChunkByCoord(&curChunk, chunks, pos, a,b,c,A,B,C);
        if(curChunk && b >= 0 && b < 128)
        {
            block = curChunk->chunk[c*xySize+b*128+a];
            if(!(block == BLOCK_EMPTY || block == BLOCK_WATER || block == BLOCK_LAVA))
                xEmpty = false;
        }

        GetLocalCoords(&a,&b,&c,&A,&B,&C,(int)ox-1,(int)oy-1,(int)oz);
        GetChunkByCoord(&curChunk, chunks, pos, a,b,c,A,B,C);
        if(curChunk && b >= 0 && b < 128)
        {
            block = curChunk->chunk[c*xySize+b*128+a];
            if(!(block == BLOCK_EMPTY || block == BLOCK_WATER || block == BLOCK_LAVA))
                xEmpty = false;
        }

        GetLocalCoords(&a,&b,&c,&A,&B,&C,(int)ox,(int)oy-1,(int)oz+1);
        GetChunkByCoord(&curChunk, chunks, pos, a,b,c,A,B,C);
        if(curChunk && b >= 0 && b < 128)
        {
            block = curChunk->chunk[c*xySize+b*128+a];
            if(!(block == BLOCK_EMPTY || block == BLOCK_WATER || block == BLOCK_LAVA))
                zEmpty = false;
        }

        GetLocalCoords(&a,&b,&c,&A,&B,&C,(int)ox,(int)oy-1,(int)oz-1);
        GetChunkByCoord(&curChunk, chunks, pos, a,b,c,A,B,C);
        if(curChunk && b >= 0 && b < 128)
        {
            block = curChunk->chunk[c*xySize+b*128+a];
            if(!(block == BLOCK_EMPTY || block == BLOCK_WATER || block == BLOCK_LAVA))
                zEmpty = false;
        }
    }


    for(step=0;step<steps;++step)
    {
        px = sx; py = sy; pz = sz;
        sx += stepx;
        sy += stepy;
        sz += stepz;
        for(k=0;k<lenZ;++k)
        {
            for(j=0;j<lenY;++j)
            {
                for(i=0;i<lenX;++i)
                {
                    GetLocalCoords(&a,&b,&c,&A,&B,&C,x+i,y+j,z+k);
                    GetChunkByCoord(&curChunk, chunks, pos, a,b,c,A,B,C);
                    if(!curChunk || b < 0 || b >= 128)
                    {
                        sx = px;
                        sy = py;
                        sz = pz;
                        continue;
                    }
                    block = curChunk->chunk[c*xySize+b*128+a];
                    if(!CheckWalkable(block) && BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f), (float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, sx-hx,sy-hy,sz-hz,sx+hx,sy,sz+hz))
                    {
                        found = false;
                        curx = sx;
                        cury = py; // 우선순위.
                        curz = sz;
                        if(!found && !BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, curx-hx,cury-hy,curz-hz,curx+hx,cury,curz+hz))
                        {
                            sy = py;
                            found = true;
                        }

                        if(xEmpty)
                        {
                            curx = sx;
                            cury = sy;
                            curz = pz;
                            if(!found && !BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, curx-hx,cury-hy,curz-hz,curx+hx,cury,curz+hz))
                            {
                                sz = pz;
                                found = true;
                            }

                            curx = px;
                            cury = sy;
                            curz = sz;
                            if(!found && !BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, curx-hx,cury-hy,curz-hz,curx+hx,cury,curz+hz))
                            {
                                sx = px;
                                found = true;
                            }

                        }
                        else
                        {
                            curx = px;
                            cury = sy;
                            curz = sz;
                            if(!found && !BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, curx-hx,cury-hy,curz-hz,curx+hx,cury,curz+hz))
                            {
                                sx = px;
                                found = true;
                            }

                            curx = sx;
                            cury = sy;
                            curz = pz;
                            if(!found && !BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, curx-hx,cury-hy,curz-hz,curx+hx,cury,curz+hz))
                            {
                                sz = pz;
                                found = true;
                            }

                        }
                        // z를 빼면 안걸리고 x를 빼면 걸리는데, x를 따라 이동하는 거라면? 그걸 어떻게 알지..
                        // 아. 아예 안가는건 x와 z가 둘 다 걸리는 거다. z만 빼면 되는데 x를 먼저 빼두고 되는 블럭이 지나간후
                        // z도 빼야되게 되어서.
                        //
                        // "방향쪽에 있는" 블럭을 찾아서 빈 블럭을 찾고 빈블럭쪽으로는 움직이게.
                        // 빈블럭이 x쪽에 있으면 z를 먼저
                        // 빈블럭이 z쪽에 있으면 x를 먼저.

                        curx = sx;
                        cury = py;
                        curz = pz;
                        if(!found && !BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, curx-hx,cury-hy,curz-hz,curx+hx,cury,curz+hz))
                        {
                            sy = py;
                            sz = pz;
                            found = true;
                        }
                        curx = px;
                        cury = py;
                        curz = sz;
                        if(!found && !BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, curx-hx,cury-hy,curz-hz,curx+hx,cury,curz+hz))
                        {
                            sx = px;
                            sy = py;
                            found = true;
                        }

                        curx = px;
                        cury = sy;
                        curz = pz;
                        if(!found && !BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, curx-hx,cury-hy,curz-hz,curx+hx,cury,curz+hz))
                        {
                            sx = px;
                            sz = pz;
                            found = true;
                        }


                        if(!found)
                        {
                            if(BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, px-hx,py-hy,pz-hz,px+hx,py,pz+hz))
                            {
                                px = ox;
                                py = oy;
                                pz = oz;
                            }
                            *fx = px;
                            *fy = py;
                            *fz = pz;
                            free(nearbyBlocks);
                            return;
                        }
                        if(BoxBoxCollide((float)(x+i-0.19f), (float)(y+j-0.19f), (float)(z+k-0.19f),(float)(x+i)+1.19f, (float)(y+j)+1.19f, (float)(z+k)+1.19f, sx-hx,sy-hy,sz-hz,sx+hx,sy,sz+hz))
                        {
                            sx = px;
                            sy = py;
                            sz = pz;
                        }
                    }
                }
            }
        }
    }
    
    *fx = sx;
    *fy = sy;
    *fz = sz;
    free(nearbyBlocks);
}

void swap(int *a, int *b)
{
    int temp;
    temp = *b;
    *b = *a;
    *a = temp;
}
void bubblesort(int *items, int len)
{
    int swapped = true, i;
    while(swapped)
    {
        swapped = false;
        for(i=0;i<(len/2)-1;++i)
        {
            if(items[i*2+1] > items[(i+1)*2+1])
            {
                swap(&items[i*2], &items[(i+1)*2]);
                swap(&items[i*2+1], &items[(i+1)*2+1]);
                swapped = true;
            }
            else if(items[i*2+1] == items[(i+1)*2+1] && items[i*2] > items[(i+1)*2])
            {
                swap(&items[i*2], &items[(i+1)*2]);
                swap(&items[i*2+1], &items[(i+1)*2+1]);
                swapped = true;
            }
        }
    }
}

void QuatCreateFromAxisAngle(Quaternion *q, float x, float y, float z, float degrees)
{
    float angle = (degrees / 180.0) * M_PI;
    float result = sinf( angle / 2.0 );
    q->w = cosf( angle / 2.0 );
    q->x = (x * result);
    q->y = (y * result);
    q->z = (z * result);
}

void QuatCreateMatrix(Quaternion *q, float pMatrix[16])
{
    // First row
    pMatrix[ 0] = 1.0 - 2.0 * ( q->y * q->y + q->z * q->z );
    pMatrix[ 1] = 2.0 * (q->x * q->y + q->z * q->w);
    pMatrix[ 2] = 2.0 * (q->x * q->z - q->y * q->w);
    pMatrix[ 3] = 0.0;
    
    // Second row
    pMatrix[ 4] = 2.0 * ( q->x * q->y - q->z * q->w );
    pMatrix[ 5] = 1.0 - 2.0 * ( q->x * q->x + q->z * q->z );
    pMatrix[ 6] = 2.0 * (q->z * q->y + q->x * q->w );
    pMatrix[ 7] = 0.0;

    // Third row
    pMatrix[ 8] = 2.0 * ( q->x * q->z + q->y * q->w );
    pMatrix[ 9] = 2.0 * ( q->y * q->z - q->x * q->w );
    pMatrix[10] = 1.0 - 2.0 * ( q->x * q->x + q->y * q->y );
    pMatrix[11] = 0.0;

    // Fourth row
    pMatrix[12] = 0;
    pMatrix[13] = 0;
    pMatrix[14] = 0;
    pMatrix[15] = 1.0;
}

void MultMatrix(XYZ *dstV, XYZ *srcV, float mat[16])
{
    dstV->x = srcV->x*mat[0] + srcV->y*mat[1] + srcV->z*mat[2] + 1.0f*mat[3];
    dstV->y = srcV->x*mat[4] + srcV->y*mat[5] + srcV->z*mat[6] + 1.0f*mat[7];
    dstV->z = srcV->x*mat[8] + srcV->y*mat[9] + srcV->z*mat[10] + 1.0f*mat[11];
    float w = srcV->x*mat[12] + srcV->y*mat[13] + srcV->z*mat[14] + 1.0f*mat[15];
    dstV->x /= w;
    dstV->y /= w;
    dstV->z /= w;
}

void AddV2(vec2 *dst, vec2 *a, vec2 *b)
{
    dst->x = a->x+b->x;
    dst->y = a->y+b->y;
}
void SubV2(vec2 *dst, vec2 *a, vec2 *b)
{
    dst->x = a->x-b->x;
    dst->y = a->y-b->y;
}
void MultSV2(vec2 *dst, vec2 *a, float scalar)
{
    dst->x = a->x*scalar;
    dst->y = a->y*scalar;
}


void GenTrees(Chunk *chunk)
{
    unsigned char treex[500];
    unsigned char treez[500];
    int treeIdx = 0;

    srand(time(NULL));
    for(treeIdx=0;treeIdx<500;++treeIdx)
    {
        treex[treeIdx] = (rand() % 120) + 4;
        treez[treeIdx] = (rand() % 120) + 4;
    }
}
void FillTrees(Chunk *chunk, char trees[1000])
{
    int i;
    int x,y,z;
    for(i=0;i<500;++i)
    {
        x = trees[i*2];
        z = trees[i*2+1];
        if(0 <= x && x < 128 && 0 <= z && z < 128)
            y = chunk->heights[z*128+x];
        else
            continue;
        if(0 <= (x-1) && (x+1) < 128 && 0 <= y && (y+5) < 128 && 0 <= (z-1) && (z+1) < 128 && chunk->chunk[z*128*128+y*128+x] == BLOCK_GRASS)
        {
            chunk->chunk[z*128*128+y*128+x] = BLOCK_DIRT;
            chunk->chunk[z*128*128+(y+1)*128+x] = BLOCK_LOG;
            chunk->chunk[z*128*128+(y+2)*128+x] = BLOCK_LOG;
            chunk->chunk[z*128*128+(y+3)*128+x] = BLOCK_LOG;
            chunk->chunk[z*128*128+(y+4)*128+x] = BLOCK_LOG;

            chunk->chunk[(z-1)*128*128+(y+4)*128+x] = BLOCK_LEAVES;
            chunk->chunk[(z+1)*128*128+(y+4)*128+x] = BLOCK_LEAVES;
            chunk->chunk[z*128*128+(y+4)*128+x-1] = BLOCK_LEAVES;
            chunk->chunk[z*128*128+(y+4)*128+x+1] = BLOCK_LEAVES;
            chunk->chunk[(z-1)*128*128+(y+4)*128+x-1] = BLOCK_LEAVES;
            chunk->chunk[(z+1)*128*128+(y+4)*128+x+1] = BLOCK_LEAVES;
            chunk->chunk[(z+1)*128*128+(y+4)*128+x-1] = BLOCK_LEAVES;
            chunk->chunk[(z-1)*128*128+(y+4)*128+x+1] = BLOCK_LEAVES;

            chunk->chunk[(z-1)*128*128+(y+5)*128+x] = BLOCK_LEAVES;
            chunk->chunk[(z+1)*128*128+(y+5)*128+x] = BLOCK_LEAVES;
            chunk->chunk[z*128*128+(y+5)*128+x] = BLOCK_LEAVES;
            chunk->chunk[z*128*128+(y+5)*128+x-1] = BLOCK_LEAVES;
            chunk->chunk[z*128*128+(y+5)*128+x+1] = BLOCK_LEAVES;
        }
    }
}

/*
int *GenMap()
{
    Quaternion q;
    XYZ v1;
    v1.x = 1.0f;
    v1.y = 0.0f;
    v1.z = 0.0f;
    XYZ v2;
    float angle = 15.0f;
    vec2 points[50];
    points[0].x = 0.0f;
    points[0].y = 0.0f;
    int pointIdx = 1;
    float matrix[16];
    while(angle <= 270.0f)
    {
        QuatCreateFromAxisAngle(&q, 0.0f,1.0f,0.0f, angle);
        QuatCreateMatrix(&q, matrix);
        MultMatrix(&v2, &v1, matrix);
        MultScalar(&v2, &v2, (((float)(rand() % 100)) / 100.0f)+1.0f);
        points[pointIdx].x = points[pointIdx-1].x+v2.x;
        points[pointIdx].y = points[pointIdx-1].y+v2.z;
        angle += (rand() % 20)+20;
        pointIdx++;
    }
    // 이걸 float으로 만들어 fillmap에 전달하면 fillmap이 채우는 간단한코드
    //  이걸 C로 옮기면 땡 XX:
    //  음 청크 리스트 역시 뭔가 쿼드트리로 바꿔줘야 하지 않을지.
    //  너무 많이 로드하면 메모리 모자람 -_-;
    //  현재 한번에 3x3를 로드하는데 대충 4x4정도만 메모리에 가지고 있으면 됨. 더가면 어차피 로드
    //  돌아갈 가능성이 있으니 놔두고
    //
    //  자. 하여간에 그 다음엔 이 만든 산을 거꾸로 파느냐, 높이는 어디서 시작하느냐, 몇배로 늘리느냐, 위치 오프셋은 어디느냐에따라
    //  여러가지 지형이 가능할 것이고
    //  전부 풀땅으로만 채우지 말고 여러가지로 채우고, 밑으로 판 거에는 특히 물 등을 채우고 그러면 바다나 호수가 된다.
    if(pointIdx >= 4)
    {
    }
    if len(self.points) >= 4:
        1,2,3,4,5,6,7,8
        lines = []
        lines += CatmullRomSpline(self.points[0], self.points[1], self.points[2], self.points[3], 0.01)
        for i in range(len(self.points)-4):
            lines += CatmullRomSpline(self.points[i+1], self.points[i+2], self.points[i+3], self.points[i+4], 0.01)
        lines += CatmullRomSpline(self.points[-3], self.points[-2], self.points[-1] , self.points[0], 0.1)
        lines += CatmullRomSpline(self.points[-2], self.points[-1], self.points[0] , self.points[1], 0.1)
        lines += CatmullRomSpline(self.points[-1], self.points[0], self.points[1] , self.points[2], 0.1)
        //스케일 하고 정렬한다.
        leftMost = lines[0]
        rightMost = lines[0]
        topMost = lines[0]
        bottomMost = lines[0]
        for point in lines:
            if point.x < leftMost.x:
                leftMost = point
        for point in lines:
            if point.y > topMost.y:
                topMost = point
        for point in lines:
            if point.x > rightMost.x:
                rightMost = point
        for point in lines:
            if point.y < bottomMost.y:
                bottomMost = point
        xdif = leftMost.x
        ydif = bottomMost.y
        lenX = rightMost.x - leftMost.x
        lenY = topMost.y - bottomMost.y
        factorX = 32.0 / lenX
        factorY = 32.0 / lenY
        lines2 = []
        for point in lines:
            point.x -= xdif
            point.y -= ydif
            point.x *= factorX
            point.y *= factorY
            point.x = int(point.x)
            point.y = int(point.y)
            lines2 += [(point.x, point.y)]

        lines2 = list(set(lines2))

        bubblesort(lines2)
        mylines = []
        prevX,prevY = lines2[0]
        prevEndX = prevX
        mylines += [(prevX,prevY)]
        odd = False
        for point in lines2[1:]:
            if point[1] != prevY:
                if not odd:
                    mylines += [(prevX, prevY)]
                    mylines += [(point[0], point[1])]
                    prevEndX = prevX
                else:
                    mylines += [(prevEndX, prevY)]
                    mylines += [(point[0], point[1])]
            prevX = point[0]
            prevY = point[1]
            odd = not odd
        if not odd: // if even
            mylines += [(prevEndX, prevY)]

        return mylines

}
*/
