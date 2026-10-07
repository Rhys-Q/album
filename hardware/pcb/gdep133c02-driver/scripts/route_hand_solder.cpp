// Conservative grid router for REVIEW DRAFTS. KiCad DRC remains authoritative.
// Inputs: board size and rectangular pad extents generated from KiCad footprints.
#include <vector>
#include <queue>
#include <map>
#include <set>
#include <fstream>
#include <iostream>
#include <cmath>
#include <algorithm>
#include <cstdint>
#include <tuple>
using namespace std;
constexpr double G=.05; constexpr int W=2001,H=1601,L=3,N=W*H*L;
struct Pad {int net;double x,y,sx,sy;int tht;};
vector<int> occ(N,0),vocc(W*H,0),dist(N),parent(N),stamp(N,0);int tick=0; double margin=.31,path_margin=.41;
int at(int x,int y,int l){return (l*H+y)*W+x;}int px(int id){return id%W;}int py(int id){return id/W%H;}int pl(int id){return id/(W*H);}
void rect(vector<int>& a,int l,int net,double x,double y,double sx,double sy,double d){
 int x0=max(0,int(ceil((x-sx/2-d)/G))),x1=min(W-1,int(floor((x+sx/2+d)/G)));
 int y0=max(0,int(ceil((y-sy/2-d)/G))),y1=min(H-1,int(floor((y+sy/2+d)/G)));
 for(int yy=y0;yy<=y1;yy++)for(int xx=x0;xx<=x1;xx++){int z=at(xx,yy,l);if(a[z]==0||a[z]==net)a[z]=net;else a[z]=-1;}
}
void circle(int x,int y,int net,double radius,bool via,int layer){
 int r=ceil(radius/G);
 for(int yy=max(0,y-r);yy<=min(H-1,y+r);yy++)for(int xx=max(0,x-r);xx<=min(W-1,x+r);xx++)if((xx-x)*(xx-x)+(yy-y)*(yy-y)<=r*r){
  if(via){for(int l=0;l<L;l++){int z=at(xx,yy,l);if(occ[z]==0||occ[z]==net)occ[z]=net;else {occ[z]=-1;}}}
  else {int z=at(xx,yy,layer);if(occ[z]==0||occ[z]==net)occ[z]=net;else {occ[z]=-1;}}
 }
}
struct Node {int f,g,id;bool operator<(const Node&o)const{return f>o.f;}};
vector<int> route(int start,const set<int>&targets,int net){
 ++tick;priority_queue<Node>pq;dist[start]=0;stamp[start]=tick;parent[start]=-1;
 // Nearest tree target supplies a consistent lower-bound heuristic.
 auto heur=[&](int id){int best=1000000;for(int t:targets){int dx=abs(px(id)-px(t)),dy=abs(py(id)-py(t));best=min(best,10*max(dx,dy)+4*min(dx,dy)+(pl(id)==pl(t)?0:60));}return best;};
 pq.push({heur(start),0,start});int found=-1,visits=0;
 while(!pq.empty()){
  auto n=pq.top();pq.pop();if(stamp[n.id]!=tick||dist[n.id]!=n.g)continue;
  if(targets.count(n.id)){found=n.id;break;}if(++visits>1500000)break;
  int x=px(n.id),y=py(n.id),l=pl(n.id);
  auto offer=[&](int to,int cost){int g=n.g+cost;if(stamp[to]!=tick||g<dist[to]){stamp[to]=tick;dist[to]=g;parent[to]=n.id;pq.push({g+heur(to),g,to});}};
  for(int dx=-1;dx<=1;dx++)for(int dy=-1;dy<=1;dy++)if(dx||dy){int xx=x+dx,yy=y+dy;if(xx<4||yy<4||xx>=W-4||yy>=H-4)continue;int id=at(xx,yy,l);if(occ[id]&&occ[id]!=net)continue;if(dx&&dy){int a=occ[at(x+dx,y,l)],b=occ[at(x,y+dy,l)];if((a&&a!=net)||(b&&b!=net))continue;}offer(id,(dx&&dy?14:10)+(l==1?1:0));}
  bool clear=!vocc[y*W+x];
  // Via copper radius .35 + clearance .2 + discretization margin .05.
  for(int ly=0;ly<L&&clear;ly++)for(int dy=-4;dy<=4&&clear;dy++)for(int dx=-4;dx<=4;dx++)if(dx*dx+dy*dy<=16){int xx=x+dx,yy=y+dy;if(xx<4||yy<4||xx>=W-4||yy>=H-4){clear=false;break;}int v=occ[at(xx,yy,ly)];if(v&&v!=net){clear=false;break;}}
  if(clear)for(int ly=0;ly<L;ly++)if(ly!=l)offer(at(x,y,ly),80);
 }
 if(found<0)return {};vector<int>path;for(int i=found;i>=0;i=parent[i])path.push_back(i);reverse(path.begin(),path.end());return path;
}

int main(int argc,char**argv){
 if(argc!=3 && argc!=4)return 2; if(argc==4){margin=.46;path_margin=.56;}ifstream input(argv[1]);string kind;map<int,pair<int,set<int>>>jobs;vector<tuple<int,int,int>>starts;
 while(input>>kind){
  if(kind=="P"){int net,tht;double x,y,sx,sy;input>>net>>x>>y>>sx>>sy>>tht;for(int l=0;l<L;l++)if(l==0||tht)rect(occ,l,net?net:-9999,x,y,sx,sy,margin);}
  if(kind=="T"){int net,l;double x1,y1,x2,y2,width;input>>net>>l>>x1>>y1>>x2>>y2>>width;double len=hypot(x2-x1,y2-y1);int steps=max(1,int(ceil(len/G)));for(int i=0;i<=steps;i++){double t=double(i)/steps;circle(round((x1+(x2-x1)*t)/G),round((y1+(y2-y1)*t)/G),net,width/2+margin,false,l);}}
  if(kind=="H"){double x,y,drill;input>>x>>y>>drill;int cx=round(x/G),cy=round(y/G),r=ceil((drill/2+.43)/G);for(int yy=max(0,cy-r);yy<=min(H-1,cy+r);yy++)for(int xx=max(0,cx-r);xx<=min(W-1,cx+r);xx++)if((xx-cx)*(xx-cx)+(yy-cy)*(yy-cy)<=r*r)vocc[yy*W+xx]=1;}
  if(kind=="S"){int net,l,grp;double x,y;input>>net>>x>>y>>l>>grp;starts.push_back({net,at(round(x/G),round(y/G),l),grp});}
  if(kind=="E"){int net,l,grp;double x,y;input>>net>>x>>y>>l>>grp;jobs[grp].second.insert(at(round(x/G),round(y/G),l));}
 }
 ofstream out(argv[2]);int bad=0;
 set<int>done;for(auto &st:starts){int net=get<0>(st),start=get<1>(st),grp=get<2>(st);if(done.count(grp))continue;auto targets=jobs[grp].second;
  // Occupancy already contains .31 mm trace-center spacing; .20 mm additional
  // via radius equals .30 copper radius + .21 clearance to existing geometry.
  if(occ[start] && occ[start]!=net){cerr<<"blocked start "<<net<<" "<<px(start)*G<<","<<py(start)*G<<" layer "<<pl(start)<<" occ "<<occ[start]<<"\n";continue;}
  auto path=route(start,targets,net);
  if(path.empty())continue;done.insert(grp);
  out<<"PATH "<<net<<" "<<path.size()<<"\n";for(int id:path)out<<px(id)*G<<" "<<py(id)*G<<" "<<pl(id)<<"\n";
  for(int j=0;j<(int)path.size();j++){int id=path[j];bool via=j&&pl(path[j-1])!=pl(id);if(via){int cx=px(id),cy=py(id);for(int yy=max(0,cy-12);yy<=min(H-1,cy+12);yy++)for(int xx=max(0,cx-12);xx<=min(W-1,cx+12);xx++)if((xx-cx)*(xx-cx)+(yy-cy)*(yy-cy)<=144)vocc[yy*W+xx]=1;}circle(px(id),py(id),net,via?.60:path_margin,via,pl(id));}
  cerr<<"routed "<<net<<" "<<path.size()<<" steps\n";
 }
 set<int>expected;for(auto&st:starts)expected.insert(get<2>(st));cerr<<"completed "<<done.size()<<"/"<<expected.size()<<" connections\n";return done.size()==expected.size()?0:1;
}
