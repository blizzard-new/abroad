/* React Bits Glide Select interaction, adapted to native forms without React.
 * https://reactbits.dev/micro/glide-select — assets/licenses/react-bits-LICENSE.md
 */
(() => {
  'use strict';
  let serial=0, opened=null;
  const instances=new Set();
  const chevron='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  const check='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="m5 12 4 4 10-10"/></svg>';
  window.UniWayGlideSelect=class {
    constructor(select) {
      if(select.uniwayGlide)return select.uniwayGlide;
      select.uniwayGlide=this; instances.add(this); this.select=select;
      if(!select.id)select.id='uw-select-'+(++serial);
      this.id='uw-glide-'+(++serial);this.opened=false;this.active=0;this.typeBuffer='';
      this.root=document.createElement('span');this.root.className='glide-select';
      select.before(this.root);this.root.append(select);
      // Keep the real control in the form for validation, FormData and existing event handlers.
      select.classList.add('glide-select__native');select.tabIndex=-1;select.setAttribute('aria-hidden','true');
      this.trigger=document.createElement('button');this.trigger.type='button';this.trigger.className='glide-select__trigger';
      this.trigger.setAttribute('role','combobox');this.trigger.setAttribute('aria-haspopup','listbox');
      this.trigger.setAttribute('aria-expanded','false');this.trigger.setAttribute('aria-controls',this.id);
      this.trigger.innerHTML='<span class="glide-select__label"></span><span class="glide-select__chevron">'+chevron+'</span>';
      this.label=this.trigger.firstElementChild;
      this.menu=document.createElement('div');this.menu.className='glide-select__menu';this.menu.setAttribute('popover','auto');
      this.list=document.createElement('div');this.list.className='glide-select__list';this.list.id=this.id;this.list.setAttribute('role','listbox');
      this.menu.append(this.list);
      this.feedback=document.createElement('span');this.feedback.className='glide-select__feedback';this.feedback.id=this.id+'-error';this.feedback.setAttribute('role','alert');
      this.root.append(this.trigger,this.menu,this.feedback);
      this.trigger.addEventListener('click',()=>this.opened?this.close():this.open());
      this.trigger.addEventListener('keydown',e=>this.onKey(e));
      this.menu.addEventListener('toggle',e=>{if(e.newState==='closed')this.closed();});
      this.list.addEventListener('pointerover',e=>{const row=e.target.closest('[data-index]');if(e.pointerType!=='touch'&&row)this.activate(+row.dataset.index);});
      this.list.addEventListener('click',e=>{const row=e.target.closest('[data-index]');if(row)this.pick(+row.dataset.index);});
      select.addEventListener('change',()=>{this.feedback.textContent='';this.trigger.removeAttribute('aria-invalid');this.sync();});
      select.addEventListener('focus',()=>this.trigger.focus());
      select.addEventListener('invalid',e=>{
        e.preventDefault();this.feedback.textContent=select.validationMessage;this.trigger.setAttribute('aria-invalid','true');
        for(let p=this.root.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
        requestAnimationFrame(()=>{const first=select.form?.querySelector('input:invalid,select:invalid,textarea:invalid');if(!first||first===select)this.trigger.focus();});
      });
      // Synchronize existing application code that assigns .value / .selectedIndex without firing change.
      for(const prop of ['value','selectedIndex']) {
        const descriptor=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,prop);
        Object.defineProperty(select,prop,{configurable:true,get:()=>descriptor.get.call(select),set:value=>{descriptor.set.call(select,value);queueMicrotask(()=>this.sync());}});
      }
      this.sync();
    }
    name() {
      if(this.select.getAttribute('aria-label'))return this.select.getAttribute('aria-label');
      const ids=(this.select.getAttribute('aria-labelledby')||'').split(/\s+/).filter(Boolean);
      if(ids.length)return ids.map(id=>document.getElementById(id)?.textContent||'').join(' ');
      return [...this.select.labels].map(label=>{const clone=label.cloneNode(true);clone.querySelectorAll('select,button,.glide-select').forEach(x=>x.remove());return clone.textContent.trim();}).join(' ')||this.select.name||'選擇選項';
    }
    sync() {
      if(!this.select.isConnected)return;
      this.items=[...this.select.options];
      this.root.hidden=this.select.hidden;
      this.trigger.disabled=this.select.matches(':disabled')||!this.items.some((_,i)=>!this.disabled(i));
      if(this.opened&&(this.trigger.disabled||this.select.hidden))this.close();
      this.trigger.setAttribute('aria-label',this.name());this.list.setAttribute('aria-label',this.name());
      this.trigger.setAttribute('aria-required',String(this.select.required));
      this.trigger.setAttribute('aria-describedby',[this.select.getAttribute('aria-describedby'),this.feedback.id].filter(Boolean).join(' '));
      this.list.setAttribute('aria-multiselectable',String(this.select.multiple));
      this.label.textContent=[...this.select.selectedOptions].map(o=>o.textContent).join('、')||'選擇選項';
      const signature=JSON.stringify(this.items.map(o=>[o.label,o.value,o.selected,o.disabled,o.hidden,o.parentElement.disabled,o.parentElement.label]));
      if(signature===this.signature)return;
      this.signature=signature;this.rows=[];this.list.replaceChildren();
      this.pill=document.createElement('span');this.pill.className='glide-select__pill';this.pill.setAttribute('aria-hidden','true');this.list.append(this.pill);
      let group=null;
      this.items.forEach((item,index)=>{
        if(item.parentElement.tagName==='OPTGROUP'&&item.parentElement!==group){
          group=item.parentElement;
          const heading=document.createElement('div');heading.className='glide-select__group';heading.textContent=group.label;heading.setAttribute('role','presentation');this.list.append(heading);
        }
        const row=document.createElement('div');row.className='glide-select__option';row.id=this.id+'-'+index;row.dataset.index=index;
        row.hidden=item.hidden;
        row.setAttribute('role','option');row.setAttribute('aria-selected',String(item.selected));row.setAttribute('aria-disabled',String(this.disabled(index)));
        const label=document.createElement('span');label.className='glide-select__name';label.textContent=item.label;
        const tick=document.createElement('span');tick.className='glide-select__check';tick.setAttribute('aria-hidden','true');tick.innerHTML=check;
        row.append(label,tick);this.list.append(row);this.rows.push(row);
      });
      if(this.opened)this.activate(this.active);
    }
    disabled(index){const item=this.items[index];return !item||item.disabled||item.hidden||!!item.parentElement.disabled;}
    open() {
      this.sync();if(this.trigger.disabled)return;
      if(opened&&opened!==this)opened.close();opened=this;
      this.active=Math.max(0,this.select.selectedIndex);
      if(this.disabled(this.active))this.active=this.items.findIndex((_,i)=>!this.disabled(i));
      const r=this.trigger.getBoundingClientRect(),width=Math.min(Math.max(280,r.width),innerWidth-24);
      const below=innerHeight-r.bottom-16,above=r.top-16,top=below<240&&above>below;
      Object.assign(this.menu.style,{width:width+'px',maxHeight:Math.min(360,Math.max(80,top?above:below))+'px',left:Math.min(Math.max(12,r.left),innerWidth-width-12)+'px',top:top?'auto':r.bottom+7+'px',bottom:top?innerHeight-r.top+7+'px':'auto','--gs-origin':top?'bottom left':'top left'});
      this.menu.showPopover();this.opened=true;this.trigger.setAttribute('aria-expanded','true');this.trigger.focus({preventScroll:true});
      this.activate(this.active,true);
    }
    closed(){this.opened=false;this.trigger.setAttribute('aria-expanded','false');this.trigger.removeAttribute('aria-activedescendant');if(opened===this)opened=null;}
    close(focus=false){if(this.menu.matches(':popover-open'))this.menu.hidePopover();this.closed();if(focus)this.trigger.focus({preventScroll:true});}
    activate(index,reveal=false){
      if(this.disabled(index))return;this.active=index;const row=this.rows[index];if(!row)return;
      this.pill.style.transform='translateY('+row.offsetTop+'px)';this.pill.style.height=row.offsetHeight+'px';this.pill.style.opacity='1';
      this.rows.forEach((r,i)=>r.classList.toggle('is-active',i===index));this.trigger.setAttribute('aria-activedescendant',row.id);
      if(reveal){if(row.offsetTop<this.menu.scrollTop)this.menu.scrollTop=row.offsetTop;else if(row.offsetTop+row.offsetHeight>this.menu.scrollTop+this.menu.clientHeight-12)this.menu.scrollTop=row.offsetTop+row.offsetHeight-this.menu.clientHeight+12;}
    }
    pick(index){
      if(this.disabled(index)||this.trigger.disabled)return;
      if(this.select.multiple)this.items[index].selected=!this.items[index].selected;else this.select.selectedIndex=index;
      if(!this.select.multiple)this.close(true);
      this.select.dispatchEvent(new Event('input',{bubbles:true}));this.select.dispatchEvent(new Event('change',{bubbles:true}));this.sync();
    }
    onKey(e){
      if(!this.opened){if(['Enter',' ','ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();this.open();}return;}
      if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){
        e.preventDefault();const indexes=this.items.map((_,i)=>i).filter(i=>!this.disabled(i)),pos=indexes.indexOf(this.active);
        this.activate(e.key==='Home'?indexes[0]:e.key==='End'?indexes.at(-1):indexes[Math.max(0,Math.min(indexes.length-1,pos+(e.key==='ArrowDown'?1:-1)))],true);
      }else if(e.key==='Enter'||e.key===' '){e.preventDefault();this.pick(this.active);}
      else if(e.key==='Escape'){e.preventDefault();this.close(true);}
      else if(e.key==='Tab')this.close();
      else if(e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey){
        clearTimeout(this.typeTimer);this.typeBuffer+=e.key.toLowerCase();
        const index=this.items.findIndex((x,i)=>!this.disabled(i)&&x.textContent.toLowerCase().includes(this.typeBuffer));
        if(index>=0){e.preventDefault();this.activate(index,true);}this.typeTimer=setTimeout(()=>this.typeBuffer='',700);
      }
    }
  };
  const enhance=node=>{if(node.nodeType!==1)return;for(const select of [ ...(node.matches('select')?[node]:[]),...node.querySelectorAll('select')])if(!select.uniwayGlide)new window.UniWayGlideSelect(select);};
  function start(){
    enhance(document.body);
    new MutationObserver(records=>{
      const dirty=new Set();
      for(const record of records){
        const select=record.target.closest?.('select');if(select?.uniwayGlide)dirty.add(select.uniwayGlide);
        for(const node of record.addedNodes)enhance(node);
        if(record.target.matches?.('fieldset'))record.target.querySelectorAll('select').forEach(s=>s.uniwayGlide&&dirty.add(s.uniwayGlide));
      }
      dirty.forEach(x=>x.sync());
      for(const item of instances)if(!item.select.isConnected){item.close();instances.delete(item);}
    }).observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['disabled','hidden','required','multiple','selected','label','aria-label','aria-labelledby']});
    document.addEventListener('reset',e=>setTimeout(()=>e.target.querySelectorAll('select').forEach(s=>s.uniwayGlide?.sync()),0));
    addEventListener('resize',()=>opened?.close());
    addEventListener('scroll',e=>{if(opened&&!opened.menu.contains(e.target))opened.close();},true);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
