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

test("in-flight work locks the rubric to avoid displaying a score for changed inputs", async () => {
  let finish;
  const pending = new Promise((resolve) => { finish = resolve; });
  const dom = setup(async () => pending);
  const doc = dom.window.document;
  doc.getElementById("load-demo").click();
  assert.equal(doc.getElementById("requirements").disabled, true);
  assert.equal(doc.getElementById("resume-file").disabled, true);
  finish({ ok: true, json: async () => demo });
  await settle();
  assert.equal(doc.getElementById("requirements").disabled, false);
  assert.equal(doc.getElementById("resume-file").disabled, false);
  dom.window.close();
});

function setup(fetch) {
  const dom = new JSDOM(html, {url:"http://localhost/",runScripts:"outside-only"});
  dom.window.fetch = fetch;
  dom.window.eval(script);
  return dom;
}

const jdDraft = {
  title: "Software Engineering Trainee",
  requirements: [{ skill: "Java OR Python", alternatives: ["Java", "Python"], importance: "required", weight: 1 }],
  minimum_years: 0, experience_weight: 0,
  warnings: ["Review this draft."],
  fields: [{ field: "Job title", value: "Software Engineering Trainee", evidence: { line: 1, text: "Role: Software Engineering Trainee" } }],
};

test("JD extraction previews source evidence and only applies after a review action", async () => {
  let calls = 0;
  const dom = setup(async (url, options) => {
    calls++;
    assert.equal(url, "/api/job/extract");
    assert.equal(options.body.get("text"), "Role: Software Engineering Trainee");
    return { ok: true, json: async () => ({ draft: jdDraft }) };
  });
  const doc = dom.window.document;
  doc.getElementById("job-title").value = "Original role";
  doc.getElementById("jd-text").value = "Role: Software Engineering Trainee";
  doc.getElementById("extract-jd").click();
  assert.equal(doc.getElementById("resume-file").disabled, true);
  await settle();
  assert.equal(doc.getElementById("job-title").value, "Original role");
  assert.equal(doc.getElementById("jd-draft").hidden, false);
  assert.match(doc.getElementById("jd-evidence").textContent, /L1: Role:/);
  doc.getElementById("apply-jd").click();
  assert.equal(doc.getElementById("job-title").value, jdDraft.title);
  assert.equal(doc.getElementById("requirements").value, "Java OR Python | required | 1");
  assert.equal(doc.getElementById("minimum-years").value, "0");
  assert.equal(doc.getElementById("report-output").hidden, true);
  assert.equal(calls, 1);
  doc.getElementById("jd-text").dispatchEvent(new dom.window.Event("input", { bubbles: true }));
  assert.equal(doc.getElementById("apply-jd").disabled, true);
  assert.equal(doc.getElementById("jd-draft").hidden, true);
  dom.window.close();
});

test("JD preview treats source and warning markup as text", async () => {
  const draft = { ...jdDraft, title: "<img src=x onerror=alert(1)>", requirements: [], warnings: ["<script>bad()</script>"], fields: [] };
  const dom = setup(async () => ({ ok: true, json: async () => ({ draft }) }));
  const doc = dom.window.document;
  doc.getElementById("extract-jd").click();
  await settle();
  assert.match(doc.getElementById("jd-draft-summary").textContent, /<img/);
  assert.equal(doc.getElementById("jd-draft").querySelector("img"), null);
  assert.match(doc.getElementById("jd-draft-skills").textContent, /manually/);
  dom.window.close();
});

test("JD extraction failure restores controls and permits retry", async () => {
  let calls = 0;
  const dom = setup(async () => {
    calls++;
    return calls === 1 ? { ok: false, status: 400, json: async () => ({ error: { message: "No usable text." } }) } : { ok: true, json: async () => ({ draft: jdDraft }) };
  });
  const doc = dom.window.document;
  doc.getElementById("extract-jd").click(); await settle();
  assert.equal(doc.getElementById("error").textContent, "No usable text.");
  assert.equal(doc.getElementById("extract-jd").disabled, false);
  doc.getElementById("extract-jd").click(); await settle();
  assert.equal(doc.getElementById("error").hidden, true);
  assert.equal(doc.getElementById("apply-jd").disabled, false);
  dom.window.close();
});

test("OR syntax reaches Python as one alternative group", async () => {
  const dom = setup(async (url, options) => {
    const job = JSON.parse(options.body.get("job_json"));
    assert.equal(job.requirements.length, 1);
    assert.deepEqual(job.requirements[0].alternatives, ["Java", "Python"]);
    return { ok: true, json: async () => result };
  });
  const doc = dom.window.document;
  doc.getElementById("requirements").value = "Java OR Python | required | 3";
  doc.getElementById("analysis-form").dispatchEvent(
    new dom.window.Event("submit", { cancelable: true }),
  );
  await settle();
  assert.equal(doc.getElementById("error").hidden, true);
  assert.equal(doc.getElementById("report-output").hidden, false);
  dom.window.close();
});

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
