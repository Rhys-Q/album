import re,json
class Q(str):pass
def parse(s):
 ts=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s);stack=[];root=None
 for t in ts:
  if t=='(':
   a=[]
   if stack:stack[-1].append(a)
   stack.append(a)
  elif t==')':
   a=stack.pop()
   if not stack:root=a
  else:stack[-1].append(Q(json.loads(t)) if t.startswith('"') else t)
 return root
def dump(a):
 if isinstance(a,list):return '('+' '.join(dump(t) for t in a)+')'
 if isinstance(a,Q):return json.dumps(str(a),ensure_ascii=False)
 return str(a)
def kids(a,k):return [x for x in a if isinstance(x,list) and x and x[0]==k]
def one(a,k):return next(iter(kids(a,k)),None)
