"""Optional offline browser checks: pip install -r requirements-qa.txt; playwright install chromium."""
from pathlib import Path
import json,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def main():
 errors=[];requests=[];checks=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
  page.on('pageerror',lambda error:errors.append(str(error)))
  page.on('request',lambda request:requests.append(request.url))
  for name,n in [('index.html',3),('candidates.html',1),('candidate_detail.html',3)]:
   page.goto((ROOT/'interactive'/name).as_uri())
   page.wait_for_function(f'document.querySelectorAll(".js-plotly-plot").length==={n}')
   assert page.locator('.js-plotly-plot').count()==n
   checks.append(name+': rendered')
   if name=='candidates.html':
    page.locator('.updatemenu-header').click()
    page.locator('.updatemenu-dropdown-button').filter(has_text='ŠANCE').click()
    assert page.evaluate('Array.from(document.querySelector(".js-plotly-plot").data).filter(d=>d.visible===true)[0].x.length')==15
    page.evaluate('Plotly.Fx.hover(document.querySelector(".js-plotly-plot"),[{curveNumber:2,pointNumber:0}])')
    assert 'Pozorováno:' in page.locator('.hoverlayer').text_content()
    checks.append('party dropdown and candidate hover')
   if name=='candidate_detail.html':
    page.wait_for_function('!rendering && !pending')
    assert page.locator('#candidate option').count()==120
    assert page.locator('#minimum').inner_text()=='88'
    assert page.locator('#votes').inner_text()=='383'
    for party in page.locator('#party option').all_text_contents()[1:]:
     page.select_option('#party',label=party)
     assert page.locator('#candidate option').count()==15
    page.select_option('#party',label='Všechny')
    page.fill('#search','Červená')
    page.wait_for_function('!rendering && !pending')
    assert page.locator('#candidate option').count()==1
    assert page.locator('#votes').inner_text()=='383'
    page.fill('#search','zzzxyznotfound')
    page.wait_for_function('!rendering && !pending')
    assert page.locator('#candidate option').count()==0
    assert page.locator('#votes').inner_text()=='—'
    assert not page.locator('#components').is_visible()
    page.fill('#search','')
    page.select_option('#candidate',value='01-10')
    page.wait_for_function('!rendering && !pending')
    assert page.locator('#components').is_visible()
    assert page.evaluate('document.getElementById("components").layout.title.text').startswith('Složení hlasů')
    checks.append('120 candidates; all eight party filters; search; empty state; plot titles')
    page.screenshot(path=str(ROOT/'results/ui_desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_function('["components","sensitivity","distribution"].every(k=>{const d=document.getElementById(k);return d._fullLayout.width<400 && d.querySelector(".main-svg")}) && document.documentElement.scrollHeight>1700 && !rendering && !pending')
    assert page.evaluate('document.documentElement.scrollWidth')<=390
    page.screenshot(path=str(ROOT/'results/ui_mobile.png'),full_page=True)
    checks.append('desktop and mobile screenshots')
  assert not errors,errors
  assert not [u for u in requests if u.startswith(('https://','http://'))],requests
  result={'status':'passed','browser':browser.version,'checks':checks,'javascript_errors':errors,'external_network_requests':0}
  (ROOT/'results/ui_smoke.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
  print(json.dumps(result,ensure_ascii=False));browser.close()
if __name__=='__main__':main()
