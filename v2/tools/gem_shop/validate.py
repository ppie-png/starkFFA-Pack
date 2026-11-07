import re,subprocess,os,sys
base='/tmp/claude-0/-home-claude/f196a605-ce72-5550-83a8-35be259707e7/scratchpad/sh'
v263=open('text_263.vsh').read(); v121=open('rendertype_text_12111.vsh').read()
def expand(src, incdir, pat):
    seen=set()
    def rep(m):
        name=m.group(1).split(':')[1]
        if name in seen: return ''
        seen.add(name)
        t=open(os.path.join(incdir,name)).read()
        return re.sub(r'^#version.*$','',t,flags=re.M)
    return re.sub(pat, rep, src, flags=re.M)
os.makedirs('/tmp/glsl',exist_ok=True)
ok=True
e263=expand(v263, base+'/b/assets/minecraft/shaders/include', r'^#include <([^>]+)>[ \t]*$')
for defs in [[],['IS_GUI'],['IS_SEE_THROUGH'],['IS_GUI','IS_GRAYSCALE'],['IS_GRAYSCALE','IS_SEE_THROUGH']]:
    p='/tmp/glsl/t263_%s.vert'%('_'.join(defs) or 'world')
    open(p,'w').write(e263)
    cmd=['glslangValidator','-V','--target-env','vulkan1.2','--amb','--aml','-S','vert','-o','/tmp/glsl/out.spv']+['-D'+d for d in defs]+[p]
    r=subprocess.run(cmd,capture_output=True,text=True); print('26.3',defs,'rc',r.returncode, (r.stdout+r.stderr).strip().replace(p,'')[-700:])
    ok &= r.returncode==0
e121=expand(v121, base+'/a/assets/minecraft/shaders/include', r'^#moj_import <([^>]+)>[ \t]*$')
p='/tmp/glsl/t121.vert'; open(p,'w').write(e121)
r=subprocess.run(['glslangValidator','-S','vert',p],capture_output=True,text=True); print('1.21.11 GL330 rc',r.returncode,(r.stdout+r.stderr).strip().replace(p,'')[-700:])
ok &= r.returncode==0
print('ALL OK' if ok else 'FAILED')
