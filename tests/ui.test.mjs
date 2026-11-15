/** DOM-level UI regression checks. Real browser rendering is verified separately. */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { JSDOM } from "jsdom";

const html = await readFile(new URL("../app/templates/index.html", import.meta.url), "utf8");
const script = await readFile(new URL("../app/static/app.js", import.meta.url), "utf8");
const settle = () => new Promise((resolve) => setTimeout(resolve, 20));
const demo = {text:"Alex Morgan\nalex@example.com\nSKILLS\nPython",as_of:"2025-01-01",
  job:{title:"Python Engineer",requirements:[{skill:"Python",importance:"required",weight:3}],minimum_years:2,experience_weight:20}};
const result = {report:{id:"a".repeat(32),match_score:60},html:"<h2>Python Engineer</h2><p>60 points</p>"};

function setup(fetch) {
  const dom = new JSDOM(html, {url:"http://localhost/",runScripts:"outside-only"});
  dom.window.fetch = fetch;
  dom.window.eval(script);
  return dom;
}

test("sample loads structured rubric and resume without silently analyzing", async () => {
  let calls=0;
  const dom=setup(async(url)=>{calls++;assert.equal(url,"/api/demo");return {ok:true,json:async()=>demo};});
  const doc=dom.window.document;
  doc.getElementById("load-demo").click();await settle();
  assert.equal(doc.getElementById("job-title").value,"Python Engineer");
  assert.equal(doc.getElementById("requirements").value,"Python | required | 3");
  assert.equal(doc.getElementById("resume-text").value,demo.text);
  assert.equal(doc.getElementById("analyze-button").disabled,false);
  assert.equal(calls,1);dom.window.close();
});

test("analysis sends actual form data and renders server report; edits invalidate export",async()=>{
  const dom=setup(async(url,options)=>{
    if(url==="/api/demo")return {ok:true,json:async()=>demo};
    assert.equal(url,"/api/analyze");assert.equal(options.method,"POST");
    const job=JSON.parse(options.body.get("job_json"));
    assert.equal(job.requirements[0].weight,3);
    assert.equal(options.body.get("text"),demo.text);
    return {ok:true,json:async()=>result};
  });
  const doc=dom.window.document;
  doc.getElementById("load-demo").click();await settle();
  doc.getElementById("analysis-form").dispatchEvent(new dom.window.Event("submit",{cancelable:true}));await settle();
  assert.equal(doc.getElementById("report-output").hidden,false);
  assert.match(doc.getElementById("report-output").textContent,/60 points/);
  assert.equal(doc.getElementById("export-bar").hidden,false);
  doc.getElementById("job-title").dispatchEvent(new dom.window.Event("input",{bubbles:true}));
  assert.equal(doc.getElementById("export-bar").hidden,true);dom.window.close();
});

test("invalid rubric fails before transmitting and leaves controls usable",async()=>{
  let calls=0;const dom=setup(async()=>{calls++;});const doc=dom.window.document;
  doc.getElementById("requirements").value="Python | mandatory | 99";
  doc.getElementById("analysis-form").dispatchEvent(new dom.window.Event("submit",{cancelable:true}));await settle();
  assert.equal(calls,0);assert.match(doc.getElementById("error").textContent,/Requirement line 1/);
  assert.equal(doc.getElementById("analyze-button").disabled,false);dom.window.close();
});

test("network failure is actionable and never inserts raw error text as HTML",async()=>{
  const dom=setup(async()=>{throw new Error("private stack trace");});const doc=dom.window.document;
  doc.getElementById("load-demo").click();await settle();
  assert.match(doc.getElementById("error").textContent,/Connection unavailable/);
  assert.doesNotMatch(doc.getElementById("error").textContent,/private stack/);
  assert.equal(doc.getElementById("load-demo").disabled,false);dom.window.close();
});

test("server validation is shown as escaped text",async()=>{
  const dom=setup(async()=>({ok:false,status:422,json:async()=>({error:{message:"<img src=x onerror=bad> invalid"}})}));
  const doc=dom.window.document;doc.getElementById("load-demo").click();await settle();
  assert.equal(doc.getElementById("error").querySelector("img"),null);
  assert.match(doc.getElementById("error").textContent,/<img/);dom.window.close();
});
