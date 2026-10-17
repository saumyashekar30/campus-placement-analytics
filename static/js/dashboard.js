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
    // Oracle connection attempts can stall; never let a database outage freeze the UI.
    const timeout = new AbortController();
    const onAbort = () => timeout.abort();
    const timer = setTimeout(() => timeout.abort(), 4500);
    if (signal) {
      if (signal.aborted) onAbort();
      else signal.addEventListener('abort', onAbort, {once:true});
    }
    try {
      const response = await fetch(`${root}${path}`, {
        headers:{Accept:'application/json'}, signal:timeout.signal
      });
      if (!response.ok) throw new Error(`API returned HTTP ${response.status}`);
      const result = await response.json();
      if (result.status === 'error' || result.success === false)
        throw new Error(result.error || result.message || 'Service unavailable');
      return result;
    } catch(err) {
      if (timeout.signal.aborted && !signal?.aborted)
        throw new Error('The analytics service did not respond in time.');
      throw err;
    } finally {
      clearTimeout(timer);
      if (signal) signal.removeEventListener('abort',onAbort);
    }
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

  // Synthetic data is available for UI testing even with no Oracle instance.
  // Never present the preview as real placement statistics.
  function populateSelect(id, options) {
    const control = $(id);
    const selected = control.value;
    while (control.options.length > 1) control.remove(1);
    options.forEach(item => control.add(new Option(item.label, item.value)));
    control.value = selected;
    if (control.selectedIndex < 0) control.value = '';
  }

  function useSampleFilterOptions() {
    populateSelect('branch-filter',demo.branches.map(b => ({value:b.branch,label:b.branch})));
    populateSelect('company-filter',demo.companies.map((c,i) => ({value:String(i+1),label:c.company_name})));
    populateSelect('year-filter',[{value:'2026',label:'2026 (sample)'},{value:'2025',label:'2025 (empty sample)'}]);
  }

  async function loadFilterOptions() {
    try {
      const r=await json('/filters');
      if(preview) return;
      filterOptions=r.data;
      populateSelect('branch-filter',(r.data.branches||[]).map(x=>({value:x,label:x})));
      populateSelect('company-filter',(r.data.companies||[]).map(x=>({value:x.company_id,label:x.company_name})));
      populateSelect('year-filter',(r.data.years||[]).map(x=>({value:x,label:x})));
    } catch(e) {
      // The offline preview supplies its own clearly marked filter options.
    }
  }

  function filteredSample() {
    const f=filters();
    const result=structuredClone(demo);
    if (f.year && f.year !== '2026') {
      result.summary={students:0,placed:0,placement_rate:0,applications:0,selected:0,rejected:0,pending:0,highest_package:0,average_package:0,lowest_package:0};
      result.branches=[];result.companies=[];result.statuses=[];result.recent=[];
      result.interviews={total:0,passed:0,failed:0,pending:0,scheduled:0,success_rate:0,rounds:[]};
      return result;
    }
    const branch=demo.branches.find(b=>b.branch===f.branch);
    const company=demo.companies[Number(f.company)-1];
    const bf=branch ? branch.total_students/demo.summary.students : 1;
    const cf=company ? company.students_placed/demo.summary.placed : 1;
    const scale=bf*cf;
    if (branch) result.branches=[branch];
    if (company) result.companies=[company];
    if (company && !branch)
      result.branches=result.branches.map(b=>({...b,
        placed_students:Math.round(b.placed_students*cf),
        placement_percentage:Math.round(b.placement_percentage*cf*100)/100}));
    if (branch && !company)
      result.companies=result.companies.map(c=>({...c,
        offers_made:Math.round(c.offers_made*bf),
        students_placed:Math.round(c.students_placed*bf)}));
    if (branch && company)
      result.companies=[{...company,
        offers_made:Math.round(company.offers_made*bf),
        students_placed:Math.round(company.students_placed*bf)}];
    const students=branch ? branch.total_students : demo.summary.students;
    const placed=Math.min(students,Math.round((branch ? branch.placed_students:demo.summary.placed)*cf));
    const applications=Math.round(demo.summary.applications*scale);
    let remaining=applications;
    result.statuses=demo.statuses.map((s,i)=>{
      const count=i===demo.statuses.length-1?remaining:Math.min(remaining,Math.round(s.count*scale));
      remaining-=count;
      return {...s,count};
    });
    const statuses=Object.fromEntries(result.statuses.map(s=>[s.status,s.count]));
    result.summary={
      ...demo.summary,students,placed,
      placement_rate:students?Math.round(placed*10000/students)/100:0,
      applications,selected:statuses.Selected||0,rejected:statuses.Rejected||0,
      pending:applications-(statuses.Selected||0)-(statuses.Rejected||0),
      highest_package:company?company.average_package:demo.summary.highest_package,
      average_package:company?company.average_package:demo.summary.average_package,
      lowest_package:company?company.average_package:demo.summary.lowest_package
    };
    result.recent=demo.recent.filter(a=>(!branch||a.branch===branch.branch)
       &&(!company||a.company_name===company.company_name));
    const ix=result.interviews;
    for(const key of ['passed','failed','scheduled','pending'])
      ix[key]=Math.round(ix[key]*scale);
    ix.total=ix.passed+ix.failed+ix.scheduled+ix.pending;
    ix.success_rate=ix.passed+ix.failed?Math.round(ix.passed*10000/(ix.passed+ix.failed))/100:0;
    ix.rounds=ix.rounds.map(r=>({...r,passed:Math.round(r.passed*scale),failed:Math.round(r.failed*scale)}));
    return result;
  }

  function updateSample() {
    if (!preview) return;
    render(filteredSample());
    status('ready','Sample preview — all figures are synthetic');
    setText('status-time','Not live data');
  }

  async function load() {
    preview=false;
    $('demo-banner').hidden=true;
    const f=filters(),id=++requestId;
    controller?.abort();
    controller=new AbortController();
    clearError();
    status('loading',hasFilter(f)?'Applying Oracle database filters…':'Connecting to Oracle analytics…');
    try {
      if (hasFilter(f)) {
        const q=new URLSearchParams(Object.entries(f).filter(([,v])=>v));
        const scoped=await json('/dashboard-scoped?'+q,controller.signal);
        if(id!==requestId)return;
        render(normalizeScoped(scoped));
        status('ready','Showing filtered Oracle analytics');
      } else {
        // Check one team API before calling six more. When Oracle is offline,
        // seven simultaneous connection attempts unnecessarily block the preview.
        const overview=await json('/overview',controller.signal);
        if(id!==requestId)return;
        const paths={
          applications:'/applications',placement:'/placement-summary',
          companies:'/companies',branches:'/branches',packages:'/packages',
          interviews:'/interviews'
        };
        const keys=Object.keys(paths);
        const outcomes=await Promise.allSettled(keys.map(k=>json(paths[k],controller.signal)));
        if(id!==requestId)return;
        const good={overview},failed=[];
        for(let i=0;i<keys.length;i++){
          if(outcomes[i].status==='fulfilled')good[keys[i]]=outcomes[i].value;
          else failed.push(keys[i]);
        }
        render(normalizedDefault(good));
        if(failed.length){
          status('error',`Some analytics services are unavailable (${failed.length}/${keys.length})`);
          errorBox('Some live charts are unavailable',
            `Unavailable sections: ${failed.join(', ')}. Available figures remain live; no sample data is mixed in.`);
        }else status('ready','All team analytics endpoints connected');
      }
    }catch(e){
      if(e.name==='AbortError'||id!==requestId)return;
      showDemo();
      errorBox('Oracle analytics are unavailable',
        'The dashboard has switched to a clearly labeled synthetic preview. Use Retry or Refresh after Oracle is connected.');
    }
  }

  function showDemo() {
    requestId++;
    controller?.abort();
    if (!preview) {
      // Reset filters from real database IDs when entering the demo. Sample
      // company IDs are independent from production database company IDs.
      for(const id of ['branch-filter','company-filter','year-filter'])$(id).value='';
    }
    preview=true;
    clearError();
    $('demo-banner').hidden=false;
    useSampleFilterOptions();
    updateSample();
  }

  function csvCell(v){
    const raw=String(v===null||v===undefined?'':v);
    // Prevent Excel/Sheets formula execution when exporting untrusted text.
    const safe=/^[\s]*[=+@-]/.test(raw) && !/^-?\d+(\.\d+)?$/.test(raw.trim()) ? "'"+raw : raw;
    return '"'+safe.replaceAll('"','""')+'"';
  }
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

  function reloadLive(){
    if(preview) {
      // Sample company IDs are unrelated to Oracle company IDs.
      for(const id of ['branch-filter','company-filter','year-filter'])$(id).value='';
    }
    loadFilterOptions();
    load();
  }

  function init() {
    $('refresh-btn').addEventListener('click',reloadLive);
    $('retry-btn').addEventListener('click',load);
    $('demo-btn').addEventListener('click',showDemo);
    $('sample-preview-btn').addEventListener('click',showDemo);
    $('leave-demo').addEventListener('click',reloadLive);
    $('export-btn').addEventListener('click',downloadCSV);
    for(const id of ['branch-filter','company-filter','year-filter'])
      $(id).addEventListener('change',()=>{if(preview) updateSample(); else load();});
    $('reset-filters').addEventListener('click',()=>{
      for(const id of ['branch-filter','company-filter','year-filter'])$(id).value='';
      if(preview)updateSample();else load();
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
