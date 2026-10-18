/* Small, deliberately limited Markdown renderer. All input is escaped first;
   no raw HTML, links, images, scripts or event attributes are accepted. */
(function(root){
 const escapeHTML=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function inline(s){return escapeHTML(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>');}
 function markdown(text){
  const lines=String(text??'').replace(/\r/g,'').split('\n');let html='',list=null,code=false,buffer=[];
  const closeList=()=>{if(list){html+=`</${list}>`;list=null;}};
  for(const raw of lines){const line=raw.trim();
   if(line.startsWith('```')){closeList();if(code){html+='<pre><code>'+escapeHTML(buffer.join('\n'))+'</code></pre>';buffer=[];}code=!code;continue;}
   if(code){buffer.push(raw);continue;}
   if(!line){closeList();continue;}
   if(/^[-*_]{3,}$/.test(line)){closeList();html+='<hr>';continue;}
   const head=line.match(/^#{1,6}\s+(.+)$/);if(head){closeList();html+='<h3>'+inline(head[1])+'</h3>';continue;}
   const bullet=line.match(/^(?:[-*+]\s+|\d+[.)]\s+)(.+)$/);if(bullet){const type=/^\d/.test(line)?'ol':'ul';if(list!==type){closeList();html+=`<${type}>`;list=type;}html+='<li>'+inline(bullet[1])+'</li>';continue;}
   closeList();html+='<p>'+inline(line)+'</p>';
  }
  closeList();if(buffer.length)html+='<pre><code>'+escapeHTML(buffer.join('\n'))+'</code></pre>';return html;
 }
 const api={escapeHTML,markdown};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.RippleFormat=api;
})(typeof window!=='undefined'?window:globalThis);
