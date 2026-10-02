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
using namespace std;
constexpr double G=.05; constexpr int W=2001,H=1601,L=3,N=W*H*L;
struct Pad {int net;double x,y,sx,sy;int tht;};
vector<int> occ(N,0),vocc(W*H,0),dist(N),parent(N),stamp(N,0);int tick=0;
int at(int x,int y,int l){return (l*H+y)*W+x;}int px(int id){return id%W;}int py(int id){return id/W%H;}int pl(int id){return id/(W*H);}
void rect(vector<int>& a,int l,int net,double x,double y,double sx,double sy,double d){
 int x0=max(0,int(ceil((x-sx/2-d)/G))),x1=min(W-1,int(floor((x+sx/2+d)/G)));
 int y0=max(0,int(ceil((y-sy/2-d)/G))),y1=min(H-1,int(floor((y+sy/2+d)/G)));
 for(int yy=y0;yy<=y1;yy++)for(int xx=x0;xx<=x1;xx++){int z=at(xx,yy,l);if(a[z]==0||a[z]==net)a[z]=net;else a[z]=-1;}
}
void circle(int x,int y,int net,double radius,bool via,int layer){
 int r=ceil(radius/G);
 for(int yy=max(0,y-r);yy<=min(H-1,y+r);yy++)for(int xx=max(0,x-r);xx<=min(W-1,x+r);xx++)if((xx-x)*(xx-x)+(yy-y)*(yy-y)<=r*r){
  if(via){for(int l=0;l<L;l++){int z=at(xx,yy,l);if(occ[z]==0||occ[z]==net)occ[z]=net;else {}}}
  else {int z=at(xx,yy,layer);if(occ[z]==0||occ[z]==net)occ[z]=net;else {}}
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
  bool clear=true;
  // Via copper radius .35 + clearance .2 + discretization margin .05.
  for(int ly=0;ly<L&&clear;ly++)for(int dy=-12;dy<=12&&clear;dy++)for(int dx=-12;dx<=12;dx++)if(dx*dx+dy*dy<=144){int xx=x+dx,yy=y+dy;if(xx<4||yy<4||xx>=W-4||yy>=H-4){clear=false;break;}int v=occ[at(xx,yy,ly)];if(v&&v!=net){clear=false;break;}}
  if(clear)for(int ly=0;ly<L;ly++)if(ly!=l)offer(at(x,y,ly),80);
 }
 if(found<0)return {};vector<int>path;for(int i=found;i>=0;i=parent[i])path.push_back(i);reverse(path.begin(),path.end());return path;
}
int main(int argc,char**argv){
 if(argc!=3)return 2;ifstream input(argv[1]);vector<Pad>pads;Pad p;map<int,vector<int>> nets;
 while(input>>p.net>>p.x>>p.y>>p.sx>>p.sy>>p.tht){pads.push_back(p);int net=p.net?p.net:-(10000+(int)pads.size());for(int l=0;l<L;l++)if(l==0||p.tht)rect(occ,l,net,p.x,p.y,p.sx,p.sy,.31);if(p.net)nets[p.net].push_back(at(round(p.x/G),round(p.y/G),0));}
 vector<pair<int,vector<int>>>order(nets.begin(),nets.end());sort(order.begin(),order.end(),[](auto&a,auto&b){return a.second.size()<b.second.size();});
 ofstream out(argv[2]);int good=0,bad=0;
 for(auto &kv:order){int net=kv.first;auto endpoints=kv.second;if(endpoints.size()<2)continue;set<int>tree={endpoints[0]};vector<int>pending(endpoints.begin()+1,endpoints.end());
  while(!pending.empty()){
   int bi=0,bd=10000000;for(int i=0;i<(int)pending.size();i++)for(int t:tree){int d=abs(px(t)-px(pending[i]))+abs(py(t)-py(pending[i]));if(d<bd){bd=d;bi=i;}}
   int start=pending[bi];pending.erase(pending.begin()+bi);auto path=route(start,tree,net);
   if(path.empty()){cerr<<"start occupancy "<<occ[start]<<" target occupancy "<<occ[*tree.begin()]<<" expected "<<net<<"\n";bad++;cerr<<"unrouted net "<<net<<" endpoint "<<px(start)*G<<","<<py(start)*G<<"\n";continue;}
   out<<"PATH "<<net<<" "<<path.size()<<"\n";for(int id:path){out<<px(id)*G<<" "<<py(id)*G<<" "<<pl(id)<<"\n";tree.insert(id);}
   for(int j=0;j<(int)path.size();j++){int id=path[j];bool via=j&&pl(path[j-1])!=pl(id);circle(px(id),py(id),net,via?.60:.41,via,pl(id));}
   good++;
  }
 }
 cerr<<"routed branches "<<good<<"; failed "<<bad<<"\n";return bad?1:0;
}
