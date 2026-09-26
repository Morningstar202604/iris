/* Iris Command Palette (Ctrl+Shift+P) — 纯增量 UI，复用现有全局函数。 */
(function(){
  'use strict';
  var overlay=$('irisCmdPaletteOverlay'), search=$('irisCmdSearch'), list=$('irisCmdList');
  if(!overlay||!search||!list) return;
  var items=[], activeIdx=0;

  function tr(key){
    return (typeof t==='function' ? t(key) : key);
  }

  // Skin names are brand proper nouns (Ares, Catppuccin, Charizard, ...) and stay
  // as-is in every locale; only the generic "Default" is translated.
  function skinLabel(skin){
    return skin==='default' ? tr('skin_default') : skin;
  }

  var FONT_SIZE_KEYS={default:'font_size_default',small:'font_size_small',large:'font_size_large',xlarge:'font_size_xlarge'};

  var PANELS=[
    ['chat','tab_chat'],['tasks','tab_tasks'],['kanban','tab_kanban'],
    ['skills','tab_skills'],['memory','tab_memory'],['workspaces','tab_workspaces'],
    ['profiles','tab_profiles'],['todos','tab_todos'],['insights','tab_insights'],
    ['logs','tab_logs'],['settings','tab_settings']
  ];

  function buildItems(){
    var out=[];
    PANELS.forEach(function(p){
      out.push({group:tr('cmd_palette_group_go'), title:tr(p[1]), hint:p[0], run:function(){ switchPanel(p[0],{fromRailClick:true}); close(); }});
    });
    out.push({group:tr('cmd_palette_group_actions'), title:tr('cmd_palette_new_session'), hint:'Cmd K', run:function(){
      if(typeof newSession==='function'){ newSession(); }
      close();
    }});
    out.push({group:tr('cmd_palette_group_actions'), title:tr('cmd_palette_toggle_dark'), hint:'', run:function(){
      if(typeof _pickTheme==='function'){ _pickTheme(document.documentElement.classList.contains('dark')?'light':'dark'); }
      close();
    }});
    ['default','ares','mono','graphite'].forEach(function(skin){
      out.push({group:tr('cmd_palette_group_actions'), title:tr('cmd_palette_skin').replace('{0}',skinLabel(skin)), hint:'', run:function(){
        if(typeof _applySkin==='function'){ _applySkin(skin); }
        close();
      }});
    });
    ['default','small','large','xlarge'].forEach(function(size){
      out.push({group:tr('cmd_palette_group_actions'), title:tr('cmd_palette_font_size').replace('{0}',tr(FONT_SIZE_KEYS[size]||'font_size_default')), hint:'', run:function(){
        var d=document.documentElement;
        if(size==='default') delete d.dataset.fontSize; else d.dataset.fontSize=size;
        try{ localStorage.setItem('hermes-font-size',size); }catch(e){}
        close();
      }});
    });
    out.push({group:tr('cmd_palette_group_actions'), title:tr('cmd_palette_settings'), hint:'Ctrl ,', run:function(){
      switchPanel('settings',{fromRailClick:true});
      close();
    }});
    out.push({group:tr('cmd_palette_group_actions'), title:tr('cmd_palette_search_sessions'), hint:'/', run:function(){
      close();
      var ss=$('sessionSearch');
      if(ss){ if(typeof closeMobileSidebar==='function') closeMobileSidebar(); ss.focus(); }
    }});
    // ── Iris: 预设提示词（内置 8 个 + localStorage 自定义，不造轮子直接复用输入框）──
    var builtinPrompts=[
      ['cmd_prompt_translate_en_title','cmd_prompt_translate_en_body'],
      ['cmd_prompt_translate_zh_title','cmd_prompt_translate_zh_body'],
      ['cmd_prompt_summarize_title','cmd_prompt_summarize_body'],
      ['cmd_prompt_polish_title','cmd_prompt_polish_body'],
      ['cmd_prompt_weekly_title','cmd_prompt_weekly_body'],
      ['cmd_prompt_code_review_title','cmd_prompt_code_review_body'],
      ['cmd_prompt_brainstorm_title','cmd_prompt_brainstorm_body'],
      ['cmd_prompt_plan_title','cmd_prompt_plan_body']
    ];
    var custom=[];
    try{
      var raw=localStorage.getItem('iris-prompts');
      if(raw) custom=JSON.parse(raw)||[];
    }catch(e){}
    builtinPrompts.map(function(p){ return [tr(p[0]),tr(p[1])]; })
      .concat(custom).forEach(function(pp){
      out.push({group:tr('cmd_palette_group_prompts'), title:pp[0], hint:'', run:function(){
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
