/* API-backed placement intelligence dashboard. No fabricated "live" values. */
(() => {
  'use strict';

  const root = '/analytics';
  const $ = id => document.getElementById(id);
  const charts = new Map();
  const palette = {Selected:'#21bf91',Rejected:'#f18080',Applied:'#7195eb',Shortlisted:'#9b88ee','In Review':'#e8b45b',Passed:'#21bf91',Failed:'#f18080',Scheduled:'#9bacc8',Pending:'#e8b45b'};
  const fmt = n => n === null || n === undefined || !Number.isFinite(Number(n)) ? '—' : Intl.NumberFormat('en-IN',{maximumFractionDigits:0}).format(n);
  const number = v => Number(v) || 0;
  const percent = n => n === null || n === undefined || !Number.isFinite(Number(n)) ? '—' : `${Number(n).toFixed(1)}%`;
  const money = n => n === null || n === undefined || !Number.isFinite(Number(n)) ? '—' : `₹${Number(n).toFixed(2)}`;
  let data = null, controller = null, requestId = 0, preview = false;
  let filterOptions = null;

  const demo = {
    summary:{students:840,placed:622,placement_rate:74.05,applications:1936,selected:646,rejected:325,pending:965,highest_package:32,average_package:9.8,lowest_package:3.6},
    statuses:[{status:'Selected',count:646},{status:'Shortlisted',count:382},{status:'In Review',count:293},{status:'Applied',count:290},{status:'Rejected',count:325}],
    branches:[{branch:'CSE',total_students:290,placed_students:238,placement_percentage:82.07},{branch:'IT',total_students:135,placed_students:108,placement_percentage:80},{branch:'ECE',total_students:175,placed_students:124,placement_percentage:70.86},{branch:'MECH',total_students:145,placed_students:94,placement_percentage:64.83},{branch:'EEE',total_students:95,placed_students:58,placement_percentage:61.05}],
    companies:[{company_name:'Microsoft',offers_made:87,students_placed:75,average_package:23.5},{company_name:'Accenture',offers_made:113,students_placed:101,average_package:7.8},{company_name:'TCS',offers_made:156,students_placed:139,average_package:5.4},{company_name:'Amazon',offers_made:79,students_placed:68,average_package:22.1},{company_name:'Deloitte',offers_made:108,students_placed:99,average_package:9.2}],
    interviews:{total:1192,passed:668,failed:238,scheduled:164,pending:122,success_rate:73.73,rounds:[{round_name:'Aptitude',round_number:1,passed:301,failed:81},{round_name:'Technical',round_number:2,passed:247,failed:112},{round_name:'HR',round_number:3,passed:120,failed:45}]},
    recent:[{student_name:'Aarav Sharma',branch:'CSE',company_name:'Microsoft',application_date:'2026-10-10',status:'Selected'},{student_name:'Diya Rao',branch:'ECE',company_name:'Accenture',application_date:'2026-10-09',status:'Shortlisted'},{student_name:'Rohan Mehta',branch:'IT',company_name:'Amazon',application_date:'2026-10-08',status:'In Review'},{student_name:'Ananya Gupta',branch:'CSE',company_name:'Deloitte',application_date:'2026-10-07',status:'Selected'}]
  };

  function setText(id, value) { $(id).textContent = value; }
  function filters() { return {branch:$('branch-filter').value,company:$('company-filter').value,year:$('year-filter').value}; }
  function hasFilter(f) { return Boolean(f.branch || f.company || f.year); }
  function status(state, message) {
    $('status-strip').className = `status-strip ${state}`;
    setText('status-message', message);
    setText('status-time', state === 'loading' ? '' : `Updated ${new Intl.DateTimeFormat('en-IN',{hour:'2-digit',minute:'2-digit'}).format(new Date())}`);
  }
  function errorBox(title, message) {
    $('error-box').hidden = false;
    setText('error-title', title);
    setText('error-detail', message);
  }
  function clearError() { $('error-box').hidden = true; }
  async function json(path, signal) {
    const response = await fetch(`${root}${path}`,{headers:{Accept:'application/json'},signal});
    if (!response.ok) throw new Error(`API returned HTTP ${response.status}`);
    const result = await response.json();
    if (result.status === 'error' || result.success === false) throw new Error(result.error || result.message || 'Service unavailable');
    return result;
  }
  const ready = () => typeof window.Chart !== 'undefined';

  function chart(id, type, labels, datasets, options = {}) {
    if (charts.has(id)) { charts.get(id).destroy(); charts.delete(id); }
    if (!ready() || !labels.length) return;
    const canvas = $(id);
    const instance = new Chart(canvas,{
      type,
      data:{labels,datasets},
      options:{
        responsive:true,maintainAspectRatio:false,
        animation:{duration:280},
        plugins:{legend:{display:false},tooltip:{backgroundColor:'#19273f',padding:11,cornerRadius:8,titleFont:{family:'Manrope',size:11},bodyFont:{family:'Manrope',size:11}}},
        scales:type==='doughnut'?undefined:{
          x:{grid:{display:false},border:{display:false},ticks:{color:'#8b98aa',font:{size:10,family:'Manrope'},maxRotation:0}},
          y:{beginAtZero:true,border:{display:false},grid:{color:'#f1f4f8',drawTicks:false},ticks:{color:'#8b98aa',padding:12,precision:0,font:{size:10,family:'Manrope'}}}
        },
        ...options
      }
    });
    charts.set(id,instance);
  }

  function clearCharts() { for (const inst of charts.values()) inst.destroy(); charts.clear(); }
  function showEmpty(section, empty) {
    $(section+'-empty').hidden = !empty;
    $(section+'-chart-wrap')?.classList.toggle('is-empty',empty);
  }
  function normalizedDefault(results) {
    const overview = results.overview?.summary_cards;
    const application = results.applications;
    const placement = results.placement;
    const company = results.companies?.data;
    const branch = results.branches?.data;
    const packages = results.packages?.data;
    const interviews = results.interviews?.data;
    const companyByName = new Map();
    for (const item of company?.companies || []) {
      companyByName.set(item.company_name,{
        company_name:item.company_name,
        company_id:item.company_id,
        offers_made:item.offers_made,
        students_placed:item.students_placed,
        applications:0
      });
    }
    for (const item of application?.company_distribution || []) {
      const row = companyByName.get(item.company_name) || {company_name:item.company_name,offers_made:0,students_placed:0};
      row.applications = number(item.total_applicants);
      companyByName.set(item.company_name,row);
    }
    for (const item of packages?.by_company || []) {
      const row = companyByName.get(item.company_name) || {company_name:item.company_name,offers_made:0,students_placed:0};
      row.average_package = item.average_package;
      row.highest_package = item.highest_package;
      companyByName.set(item.company_name,row);
    }
    return {
      summary:overview?{
        students:overview.total_students,placed:overview.uniquely_placed_students,
        placement_rate:overview.placement_percentage,applications:overview.total_applications,
        selected:overview.selected_applications,rejected:overview.rejected_applications,
        pending:overview.pending_applications,
        highest_package:overview.package_stats?.highest_package_lpa,
        average_package:packages?.overall?.average_package ?? overview.package_stats?.avg_package_lpa,
        lowest_package:packages?.overall?.lowest_package ?? overview.package_stats?.lowest_package_lpa
      }:null,
      statuses:application?.status_distribution || results.overview?.status_distribution || [],
      branches:branch?.branches || placement?.branch_summary || [],
      companies:[...companyByName.values()],
      interviews:interviews || null,
      recent:application?.recent_applications || []
    };
  }

  function normalizeScoped(payload) {
    const d=payload.data;
    return d;
  }

  function updateMetrics(s) {
    const has = Boolean(s);
    for (const [id,value] of Object.entries({
      'kpi-students':has?fmt(s.students):'—','kpi-placed':has?fmt(s.placed):'—',
      'kpi-rate-mini':has?percent(s.placement_rate):'—','kpi-applications':has?fmt(s.applications):'—',
      'kpi-selected':has?fmt(s.selected):'—','kpi-highest':has?money(s.highest_package):'—',
      'featured-placed':has?fmt(s.placed):'—',
      'featured-unplaced':has?fmt(Math.max(0,number(s.students)-number(s.placed))):'—',
      'featured-rate':has?percent(s.placement_rate):'—',
      'package-max':has?money(s.highest_package):'—',
      'package-avg':has?money(s.average_package):'—',
      'package-min':has?money(s.lowest_package):'—'
    })) setText(id,value);
    $('placement-gauge').style.setProperty('--progress',has?Math.min(100,Math.max(0,number(s.placement_rate))):0);
  }

  function renderStatus(d) {
    const statuses=(d.statuses || []).filter(i=>number(i.count)>0);
    const count=statuses.reduce((v,x)=>v+number(x.count),0);
    setText('donut-count', d.summary?.applications !== undefined ? fmt(d.summary.applications) : statuses.length ? fmt(count) : '—');
    const legend=$('status-legend');
    legend.replaceChildren();
    if (!statuses.length){const p=document.createElement('p');p.className='placeholder';p.textContent='No application records for the selected filters.';legend.append(p);if(charts.has('status-chart')){charts.get('status-chart').destroy();charts.delete('status-chart');}return;}
    for(const row of statuses){
      const div=document.createElement('div');div.className='legend-row';
      const dot=document.createElement('i');dot.className='legend-dot';dot.style.background=palette[row.status]||'#9ba9b9';
      const name=document.createElement('span');name.className='legend-name';name.textContent=row.status;
      const total=document.createElement('strong');total.textContent=fmt(row.count);
      div.append(dot,name,total);legend.append(div);
    }
    chart('status-chart','doughnut',statuses.map(x=>x.status),
      [{data:statuses.map(x=>number(x.count)),backgroundColor:statuses.map(x=>palette[x.status]||'#9ba9b9'),borderColor:'#fff',borderWidth:4,hoverOffset:4}],
      {cutout:'77%',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.label}: ${fmt(c.parsed)} (${count ? (c.parsed*100/count).toFixed(1):0}%)`}}}});
  }

  function renderBranches(d) {
    const rows=(d.branches||[]).slice().sort((a,b)=>number(b.placement_percentage)-number(a.placement_percentage));
    showEmpty('branch',!rows.length);
    chart('branch-chart','bar',rows.map(x=>x.branch),[{label:'Placement rate',data:rows.map(x=>number(x.placement_percentage)),borderRadius:6,barThickness:16,backgroundColor:rows.map((_,i)=>i===0?'#25bf94':'#91c6f2')}],
      {indexAxis:'y',scales:{x:{min:0,max:100,grid:{color:'#f1f4f8'},border:{display:false},ticks:{callback:v=>v+'%',color:'#91a0b1',font:{size:10}}},y:{grid:{display:false},border:{display:false},ticks:{font:{size:10,weight:'bold'},color:'#546580'}}},
        plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.parsed.x}% placed · ${fmt(rows[c.dataIndex].placed_students)} of ${fmt(rows[c.dataIndex].total_students)} students`}}}});
  }

  function renderCompanies(d) {
    const companies=(d.companies || []).slice().sort((a,b)=>number(b.students_placed)-number(a.students_placed)).slice(0,6);
    showEmpty('recruiter',!companies.length);
    chart('recruiter-chart','bar',companies.map(x=>x.company_name),
      [{label:'Offers',data:companies.map(x=>number(x.offers_made)),backgroundColor:'#b1cffa',borderRadius:5,barPercentage:.7},
       {label:'Placed',data:companies.map(x=>number(x.students_placed)),backgroundColor:'#24bd95',borderRadius:5,barPercentage:.7}],
       {plugins:{legend:{display:true,position:'bottom',labels:{usePointStyle:true,boxWidth:6,boxHeight:6,font:{size:10},color:'#7b8da3'}}},
        scales:{x:{grid:{display:false},border:{display:false},ticks:{maxRotation:30,minRotation:0,color:'#74869a',font:{size:10}}},y:{beginAtZero:true,grid:{color:'#f1f4f8'},border:{display:false},ticks:{precision:0,color:'#91a0b1'}}}});
  }

  function renderPackages(d) {
    const companies=(d.companies || []).filter(x=>x.average_package!==null && x.average_package!==undefined && number(x.average_package)>0).slice().sort((a,b)=>number(b.average_package)-number(a.average_package)).slice(0,6);
    showEmpty('package',!companies.length);
    chart('package-chart','bar',companies.map(x=>x.company_name),[{data:companies.map(x=>number(x.average_package)),backgroundColor:'#81b6ee',borderRadius:6,barThickness:20}],
      {plugins:{tooltip:{callbacks:{label:c=>` ₹${c.parsed.y.toFixed(2)} LPA average`}},legend:{display:false}},
        scales:{x:{grid:{display:false},border:{display:false},ticks:{color:'#8fa0b2',font:{size:10},maxRotation:20}},y:{beginAtZero:true,grid:{color:'#f1f4f8'},border:{display:false},ticks:{color:'#8fa0b2',callback:v=>'₹'+v}}}});
  }

  function renderInterviews(d) {
    const i=d.interviews || null;
    setText('interview-rate',i?percent(i.success_rate):'—');
    setText('interview-passed',i?fmt(i.passed):'—');
    setText('interview-failed',i?fmt(i.failed):'—');
    setText('interview-pending',i?fmt(number(i.pending)+number(i.scheduled)):'—');
    const rounds=i?.rounds || [];
    showEmpty('interview',!rounds.length);
    chart('interview-chart','bar',rounds.map(x=>x.round_name),
      [{label:'Passed',data:rounds.map(x=>number(x.passed)),backgroundColor:'#21bf91',borderRadius:5,barPercentage:.75},
       {label:'Failed',data:rounds.map(x=>number(x.failed)),backgroundColor:'#f49c83',borderRadius:5,barPercentage:.75}],
      {plugins:{legend:{display:true,position:'bottom',labels:{usePointStyle:true,boxWidth:6,boxHeight:6,color:'#8fa0b3',font:{size:10}}}},
       scales:{x:{grid:{display:false},border:{display:false},ticks:{color:'#8492a7',font:{size:10}}},y:{beginAtZero:true,grid:{color:'#f1f4f8'},border:{display:false},ticks:{precision:0,color:'#8492a7'}}}});
  }

  function renderRecent(d) {
    const body=$('recent-table');body.replaceChildren();
    if (!(d.recent||[]).length) {
      const tr=body.insertRow(),td=tr.insertCell();td.colSpan=5;td.className='table-placeholder';td.textContent='No applications match the current selection.';return;
    }
    for(const entry of d.recent.slice(0,8)){
      const tr=body.insertRow();
      for(const field of ['student_name','branch','company_name','application_date','status']){
        const td=tr.insertCell();
        if(field==='status'){
          const badge=document.createElement('span');
          badge.className=`table-status ${String(entry.status||'').toLowerCase().replaceAll(' ','-')}`;
          badge.textContent=entry.status||'Unknown';td.append(badge);
        }else if(field==='application_date'){
          const date=String(entry.application_date||'').slice(0,10);
          td.textContent=date ? new Date(date+'T00:00:00').toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'}) : '—';
        }else td.textContent=entry[field]||'—';
      }
    }
  }

  function render(d) {
    data=d;
    updateMetrics(d.summary);
    renderStatus(d);
    renderBranches(d);
    renderCompanies(d);
    renderPackages(d);
    renderInterviews(d);
    renderRecent(d);
    if(!ready())errorBox('Chart.js could not load','KPI values and tables remain available. Check your internet connection to enable charts.');
  }

  async function loadFilterOptions() {
    try{
      const r=await json('/filters');
      filterOptions=r.data;
      for(const [select,values] of [
        ['branch-filter',(r.data.branches||[]).map(x=>({value:x,label:x}))],
        ['company-filter',(r.data.companies||[]).map(x=>({value:x.company_id,label:x.company_name}))],
        ['year-filter',(r.data.years||[]).map(x=>({value:x,label:x}))],
      ]){
        const el=$(select),selected=el.value;
        while(el.options.length>1)el.remove(1);
        for(const x of values){const option=new Option(x.label,x.value);el.add(option);}
        el.value=selected;
      }
    }catch(e){ /* An offline database should not disable the dashboard shell. */ }
  }

  async function load() {
    preview=false;$('demo-banner').hidden=true;
    const f=filters(),id=++requestId;
    controller?.abort();controller=new AbortController();
    clearError();status('loading',hasFilter(f)?'Applying Oracle database filters…':'Fetching live placement analytics…');
    try{
      if(hasFilter(f)){
        const q=new URLSearchParams(Object.entries(f).filter(([,v])=>v));
        const scoped=await json('/dashboard-scoped?'+q,controller.signal);
        if(id!==requestId)return;
        render(normalizeScoped(scoped));
        status('ready','Showing filtered Oracle analytics');
      }else{
        const paths={
          overview:'/overview',applications:'/applications',placement:'/placement-summary',
          companies:'/companies',branches:'/branches',packages:'/packages',interviews:'/interviews'
        };
        const keys=Object.keys(paths);
        const outcomes=await Promise.allSettled(keys.map(k=>json(paths[k],controller.signal)));
        if(id!==requestId)return;
        const good={},failed=[];
        for(let i=0;i<keys.length;i++){
          if(outcomes[i].status==='fulfilled')good[keys[i]]=outcomes[i].value;
          else failed.push(keys[i]);
        }
        render(normalizedDefault(good));
        if(failed.length){
          status('error',`Some analytics services are unavailable (${failed.length}/${keys.length})`);
          errorBox('Some analytics could not be loaded',`Unavailable sections: ${failed.join(', ')}. The rest of the dashboard reflects available live data.`);
        }else status('ready','All analytics are connected to Oracle');
      }
    }catch(e){
      if(e.name==='AbortError'||id!==requestId)return;
      render({summary:null,statuses:[],branches:[],companies:[],recent:[],interviews:null});
      status('error','Analytics service unavailable');
      errorBox('Could not load filtered analytics','The database or API is unavailable for this filter combination. Try again or preview sample data.');
    }
  }

  function showDemo() {
    requestId++;controller?.abort();preview=true;clearError();
    $('demo-banner').hidden=false;
    render(structuredClone(demo));
    status('ready','Sample data preview (not connected to Oracle)');
    setText('status-time','Synthetic preview');
  }

  function csvCell(v){return '"'+String(v===null||v===undefined?'':v).replaceAll('"','""')+'"';}
  function downloadCSV() {
    if(!data){errorBox('No data to export','Load the dashboard before exporting.');return;}
    const rows=[['Record Type','Name','Branch','Company','Status','Value','Date']];
    for(const [key,value] of Object.entries(data.summary||{}))rows.push(['Summary',key,'','','',value,'']);
    for(const b of data.branches||[])rows.push(['Branch',b.branch,b.branch,'','Placed',b.placed_students,'']);
    for(const c of data.companies||[])rows.push(['Company',c.company_name,'',c.company_name,'Placed',c.students_placed,'']);
    for(const a of data.recent||[])rows.push(['Application',a.student_name,a.branch,a.company_name,a.status,'',a.application_date]);
    const csv='\ufeff'+rows.map(r=>r.map(csvCell).join(',')).join('\r\n');
    const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download=`placement-analytics-${preview?'SAMPLE-':' '}${new Date().toISOString().slice(0,10)}.csv`.replace(' ','');a.click();
    URL.revokeObjectURL(url);
  }

  function init() {
    $('refresh-btn').addEventListener('click',()=>{loadFilterOptions();load();});
    $('retry-btn').addEventListener('click',load);
    $('demo-btn').addEventListener('click',showDemo);
    $('leave-demo').addEventListener('click',load);
    $('export-btn').addEventListener('click',downloadCSV);
    for(const id of ['branch-filter','company-filter','year-filter'])$(id).addEventListener('change',load);
    $('reset-filters').addEventListener('click',()=>{
      for(const id of ['branch-filter','company-filter','year-filter'])$(id).value='';
      load();
    });
    const sidebar=$('sidebar'),shade=$('mobile-shade');
    const close=()=>{sidebar.classList.remove('open');shade.classList.remove('visible');};
    $('menu-toggle').addEventListener('click',()=>{sidebar.classList.toggle('open');shade.classList.toggle('visible');});
    shade.addEventListener('click',close);
    sidebar.querySelectorAll('a').forEach(a=>a.addEventListener('click',close));
    document.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
    loadFilterOptions();load();
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
