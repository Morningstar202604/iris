/* Iris Command Palette (Ctrl+Shift+P) — 纯增量 UI，复用现有全局函数。 */
(function(){
  'use strict';
  var overlay=$('irisCmdPaletteOverlay'), search=$('irisCmdSearch'), list=$('irisCmdList');
  if(!overlay||!search||!list) return;
  var items=[], activeIdx=0;

  var PANELS=[
    ['chat','Chat','tab_chat'],['tasks','Tasks','tab_tasks'],['kanban','Kanban','tab_kanban'],
    ['skills','Skills','tab_skills'],['memory','Memory','tab_memory'],['workspaces','Spaces','tab_workspaces'],
    ['profiles','Profiles','tab_profiles'],['todos','Todos','tab_todos'],['insights','Insights','tab_insights'],
    ['logs','Logs','tab_logs'],['settings','设置','tab_settings']
  ];

  function buildItems(){
    var out=[];
    PANELS.forEach(function(p){
      out.push({group:'跳转到', title:p[1], hint:p[0], run:function(){ switchPanel(p[0],{fromRailClick:true}); close(); }});
    });
    out.push({group:'操作', title:'新建会话', hint:'Cmd K', run:function(){
      if(typeof newSession==='function'){ newSession(); }
      close();
    }});
    out.push({group:'操作', title:'切换深色模式', hint:'', run:function(){
      if(typeof _pickTheme==='function'){ _pickTheme(document.documentElement.classList.contains('dark')?'light':'dark'); }
      close();
    }});
    ['default','ares','mono','graphite'].forEach(function(skin){
      out.push({group:'操作', title:'皮肤: '+skin, hint:'', run:function(){
        if(typeof _applySkin==='function'){ _applySkin(skin); }
        close();
      }});
    });
    ['default','small','large','xlarge'].forEach(function(size){
      out.push({group:'操作', title:'字号: '+size, hint:'', run:function(){
        var d=document.documentElement;
        if(size==='default') delete d.dataset.fontSize; else d.dataset.fontSize=size;
        try{ localStorage.setItem('hermes-font-size',size); }catch(e){}
        close();
      }});
    });
    out.push({group:'操作', title:'设置', hint:'Ctrl ,', run:function(){
      if(typeof toggle设置==='function') toggle设置();
      close();
    }});
    out.push({group:'操作', title:'搜索会话', hint:'/', run:function(){
      close();
      var ss=$('sessionSearch');
      if(ss){ if(typeof closeMobileSidebar==='function') closeMobileSidebar(); ss.focus(); }
    }});
    // ── Iris: 预设提示词（内置 8 个 + localStorage 自定义，不造轮子直接复用输入框）──
    var builtinPrompts=[
      ['翻译成英文','将下面内容翻译成地道、自然的英文，保留原意与语气：'],
      ['翻译成中文','将下面内容翻译成通顺、自然的中文，保留原意与语气：'],
      ['总结提炼','请用简洁的要点总结下面内容，突出关键结论：'],
      ['写作润色','请优化下面的文字：使表达更流畅、准确、有文采，保持原意：'],
      ['周报生成','根据下面工作内容生成一份结构清晰的周报：'],
      ['代码审查','请审查下面代码：指出 bug、安全隐患和可优化点，并给出修改建议：'],
      ['头脑风暴','针对下面主题进行头脑风暴，给出多角度的创意方案：'],
      ['规划任务','帮我制定一份可执行的计划，包含步骤、优先级和时间安排：']
    ];
    var custom=[];
    try{
      var raw=localStorage.getItem('iris-prompts');
      if(raw) custom=JSON.parse(raw)||[];
    }catch(e){}
    builtinPrompts.concat(custom).forEach(function(pp){
      out.push({group:'预设提示词', title:pp[0], hint:'', run:function(){
        close();
        var composer=$('msg');
        if(!composer||typeof composer.focus!=='function') return;
        composer.focus();
        var insert=(pp[1]||'')+'';
        if(composer.value) composer.value=composer.value.trimEnd()+(composer.value.trimEnd().endsWith('\n')?'\n\n':'\n\n')+insert;
        else composer.value=insert;
        var ev=document.createEvent('Event'); ev.initEvent('input',true,true); composer.dispatchEvent(ev);
      }});
    });
    return out;
  }

  function render(filter){
    var q=(filter||'').toLowerCase();
    items=buildItems().filter(function(it){ return !q || it.title.toLowerCase().indexOf(q)>=0 || it.group.toLowerCase().indexOf(q)>=0; });
    activeIdx=0;
    list.innerHTML='';
    var lastGroup='';
    items.forEach(function(it,i){
      if(it.group!==lastGroup){
        lastGroup=it.group;
        var g=document.createElement('div');
        g.className='iris-cmd-group';
        g.textContent=it.group;
        list.appendChild(g);
      }
      var row=document.createElement('button');
      row.type='button';
      row.className='iris-cmd-item'+(i===0?' active':'');
      row.setAttribute('role','option');
      row.setAttribute('data-idx',i);
      var t=document.createElement('span');
      t.className='iris-cmd-title';
      t.textContent=it.title;
      row.appendChild(t);
      if(it.hint){
        var k=document.createElement('span');
        k.className='iris-cmd-hint';
        k.textContent=it.hint;
        row.appendChild(k);
      }
      row.addEventListener('click',function(){ it.run(); });
      row.addEventListener('mousemove',function(){
        var prev=list.querySelector('.iris-cmd-item.active');
        if(prev) prev.classList.remove('active');
        row.classList.add('active');
        activeIdx=i;
      });
      list.appendChild(row);
    });
  }

  function highlight(){
    Array.prototype.forEach.call(list.querySelectorAll('.iris-cmd-item'),function(el){
      el.classList.toggle('active',parseInt(el.dataset.idx,10)===activeIdx);
    });
  }

  function open(){
    overlay.hidden=false;
    render('');
    search.value='';
    search.focus();
  }
  function close(){
    overlay.hidden=true;
  }
  window.irisCmdPaletteOpen=open;

  search.addEventListener('input',function(){ render(search.value); });
  search.addEventListener('keydown',function(e){
    var n=items.length;
    if(e.key==='ArrowDown'){ e.preventDefault(); activeIdx=(activeIdx+1)%n; highlight(); }
    else if(e.key==='ArrowUp'){ e.preventDefault(); activeIdx=(activeIdx-1+n)%n; highlight(); }
    else if(e.key==='Enter'&&items[activeIdx]){ e.preventDefault(); items[activeIdx].run(); }
    else if(e.key==='Escape'){ e.preventDefault(); close(); }
  });
  overlay.addEventListener('click',function(e){ if(e.target===overlay) close(); });

  document.addEventListener('keydown',function(e){
    if((e.metaKey||e.ctrlKey)&&e.shiftKey&&e.key==='P'){
      var t=e.target, tag=t&&t.tagName;
      if(tag==='INPUT'||tag==='TEXTAREA'||(t&&t.isContentEditable)) return;
      e.preventDefault();
      open();
    }
  });
})();
