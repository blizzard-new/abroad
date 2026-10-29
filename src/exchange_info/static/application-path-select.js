/* React Bits Glide Select, adapted to native JS and a scrollable popover.
 * https://reactbits.dev/micro/glide-select
 * License: assets/licenses/react-bits-LICENSE.md. No React runtime required.
 */
(() => {
  'use strict';
  const chevron='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  const check='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="m5 12 4 4 10-10"/></svg>';
  window.UniWayGlideSelect=class {
    constructor(select) {
      this.select=select;this.root=select.parentElement;this.root.classList.add('glide-select');
      this.active=0;this.opened=false;this.rows=[];this.typeBuffer='';this.typeTimer=0;
      this.trigger=document.createElement('button');
      this.trigger.type='button';this.trigger.className='glide-select__trigger';
      this.trigger.setAttribute('role','combobox');this.trigger.setAttribute('aria-haspopup','listbox');
      this.trigger.setAttribute('aria-label',select.getAttribute('aria-label'));
      this.trigger.setAttribute('aria-expanded','false');this.trigger.setAttribute('aria-controls',select.id+'-list');
      this.trigger.innerHTML='<span class="glide-select__label"></span><span class="glide-select__chevron">'+chevron+'</span>';
      this.label=this.trigger.querySelector('.glide-select__label');
      this.menu=document.createElement('div');this.menu.className='glide-select__menu';this.menu.setAttribute('popover','auto');
      this.list=document.createElement('div');this.list.className='glide-select__list';this.list.id=select.id+'-list';
      this.list.setAttribute('role','listbox');this.list.setAttribute('aria-label',select.getAttribute('aria-label'));
      this.menu.append(this.list);this.root.append(this.trigger,this.menu);select.hidden=true;
      this.trigger.addEventListener('click',()=>this.opened?this.close():this.open());
      this.trigger.addEventListener('keydown',e=>this.onKey(e));
      this.menu.addEventListener('toggle',e=>{
        if(e.newState==='closed'){
          this.opened=false;this.trigger.setAttribute('aria-expanded','false');
          this.trigger.removeAttribute('aria-activedescendant');this.menu.dataset.state='closed';
        }
      });
      this.list.addEventListener('pointerover',e=>{
        if(e.pointerType==='touch')return;
        const row=e.target.closest('[data-index]');if(row)this.activate(Number(row.dataset.index));
      });
      this.list.addEventListener('click',e=>{const row=e.target.closest('[data-index]');if(row)this.pick(Number(row.dataset.index));});
      this.root.addEventListener('animationend',e=>{if(e.animationName==='gs-swap')delete this.root.dataset.swap;});
      select.addEventListener('change',()=>this.sync());
      addEventListener('resize',()=>this.close(false));
      addEventListener('scroll',e=>{if(this.opened&&!this.menu.contains(e.target))this.close(false);},true);
      this.sync();
    }
    sync() {
      this.close(false);this.items=[...this.select.options];this.rows=[];
      this.trigger.disabled=!this.items.length;
      this.label.textContent=this.select.selectedOptions[0]?.textContent||'選擇階段';
      this.list.replaceChildren();this.pill=document.createElement('span');this.pill.className='glide-select__pill';this.pill.setAttribute('aria-hidden','true');this.list.append(this.pill);
      this.items.forEach((item,index)=>{
        const row=document.createElement('div');row.className='glide-select__option';row.id=this.select.id+'-option-'+index;row.dataset.index=index;
        row.setAttribute('role','option');row.setAttribute('aria-selected',String(item.selected));
        const number=document.createElement('span');number.className='glide-select__number';number.textContent=String(index+1).padStart(2,'0');
        const label=document.createElement('span');label.className='glide-select__name';label.textContent=item.textContent.replace(/^\d+\s*·\s*/,'');
        const tick=document.createElement('span');tick.className='glide-select__check';tick.setAttribute('aria-hidden','true');tick.toggleAttribute('data-on',item.selected);tick.innerHTML=check;
        row.append(number,label,tick);this.list.append(row);this.rows.push(row);
      });
    }
    open() {
      if(!this.items.length)return;
      this.active=Math.max(0,this.select.selectedIndex);
      const r=this.trigger.getBoundingClientRect(),width=Math.min(310,innerWidth-24);
      const below=innerHeight-r.bottom-18,above=r.top-18;
      const top=below<240&&above>below;
      const height=Math.min(360,Math.max(120,top?above:below));
      Object.assign(this.menu.style,{width:width+'px',maxHeight:height+'px',left:Math.min(Math.max(12,r.left),innerWidth-width-12)+'px',top:top?'auto':r.bottom+7+'px',bottom:top?innerHeight-r.top+7+'px':'auto','--gs-origin':top?'bottom left':'top left'});
      this.menu.dataset.state='closed';this.menu.showPopover();this.opened=true;
      this.trigger.setAttribute('aria-expanded','true');this.trigger.focus({preventScroll:true});
      this.pill.style.transition='none';this.activate(this.active,true);
      requestAnimationFrame(()=>{if(!this.opened)return;this.menu.dataset.state='open';this.pill.style.transition='';});
    }
    close(focus=false) {
      if(this.menu.matches(':popover-open'))this.menu.hidePopover();
      this.opened=false;this.trigger.setAttribute('aria-expanded','false');this.trigger.removeAttribute('aria-activedescendant');
      if(focus)this.trigger.focus({preventScroll:true});
    }
    activate(index,reveal=false) {
      this.active=Math.max(0,Math.min(this.rows.length-1,index));const row=this.rows[this.active];if(!row)return;
      this.pill.style.transform='translateY('+row.offsetTop+'px)';this.pill.style.height=row.offsetHeight+'px';this.pill.style.opacity='1';
      this.list.dataset.live='';this.trigger.setAttribute('aria-activedescendant',row.id);
      if(reveal){const top=row.offsetTop,bottom=top+row.offsetHeight;
        if(top<this.menu.scrollTop)this.menu.scrollTop=top;
        else if(bottom>this.menu.scrollTop+this.menu.clientHeight-12)this.menu.scrollTop=bottom-this.menu.clientHeight+12;
      }
    }
    pick(index) {
      if(!this.items[index])return;
      this.select.value=this.items[index].value;this.close(true);
      this.select.dispatchEvent(new Event('change',{bubbles:true}));
      this.root.dataset.swap='';
    }
    onKey(e) {
      const key=e.key;
      if(!this.opened){if(['Enter',' ','ArrowDown','ArrowUp'].includes(key)){e.preventDefault();this.open();}return;}
      if(['ArrowDown','ArrowUp','Home','End'].includes(key)){
        e.preventDefault();this.activate(key==='Home'?0:key==='End'?this.rows.length-1:this.active+(key==='ArrowDown'?1:-1),true);
      }else if(key==='Enter'||key===' '){e.preventDefault();this.pick(this.active);}
      else if(key==='Escape'){e.preventDefault();this.close(true);}
      else if(key==='Tab')this.close(false);
      else if(key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey){
        clearTimeout(this.typeTimer);this.typeBuffer+=key.toLowerCase();
        const index=this.items.findIndex(x=>x.textContent.toLowerCase().startsWith(this.typeBuffer)||x.textContent.replace(/^\d+\s*·\s*/,'').startsWith(this.typeBuffer));
        if(index>=0){e.preventDefault();this.activate(index,true);}this.typeTimer=setTimeout(()=>this.typeBuffer='',700);
      }
    }
  };
})();
