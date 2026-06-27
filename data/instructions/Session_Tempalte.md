# **D\&D SESSION DOCUMENT FORMATTING INSTRUCTIONS**

## **OVERVIEW**

**When I ask you to create a session document, format it as a dark-themed HTML file using the structure and styling defined below. This is my preferred format for all campaign session notes.**

---

## **WHEN TO USE THIS FORMAT**

**Use this format when I say things like:**

* **"Create session \[X\]"**  
* **"Write up the session"**  
* **"Format this as a session document"**  
* **"Make this into a session file"**  
* **Or when I provide session content and ask for it to be formatted**  
  ---

  ## **OUTPUT REQUIREMENTS**

1. **File type: HTML (not Word/docx)**  
2. **File name: Session\_\[NUMBER\]\_\[TITLE\_WITH\_Underscores\].html**  
3. **Deliver: Save to outputs folder and present the file**  
   ---

   ## **CONTENT STRUCTURE**

   ### **Required Sections:**

1. **Title Section \- Session number, title, date (in-game), party level**  
2. **Table of Contents \- Clickable links to all parts/scenes**  
3. **Parts & Scenes \- The actual session content broken into logical parts**  
4. **Session End \- Conclusion/cliffhanger**  
5. **DM Notes Section \- Summary, items acquired, revelations, NPCs, timeline, consequences, next session hooks**

   ### **Scene Components:**

* **Read-aloud narration \- Boxed, colored, italicized (what I read to players)**  
* **Regular narration \- Standard descriptive text**  
* **NPC Dialogue \- Color-coded by character with name labels**  
* **DM Notes \- Boxed instructions/reminders for me**  
* **Skill Checks \- Boxed with DC badges**  
* **Option Boxes \- For player choice scenarios with risk/benefit/required labels**  
  ---

  ## **STYLE SPECIFICATIONS**

  ### **IMPORTANT \- Punctuation:**

* **NEVER use em-dashes (—) \- always use regular dashes/hyphens (-) instead**  
* **This applies to all narration, dialogue, and notes**

  ### **Fonts:**

* **Headers: Arial or Verdana, bold**  
* **Body text: Arial or Verdana**  
* **Base size: 14px**  
* **Headers scale up from there (h1: 2.2em, h2: 1.6em, h3: 1.3em)**

  ### **Colors (IMPORTANT \- all must be bright/readable on dark background):**

**Backgrounds:**

* **Page background: \#1a1a1a**  
* **Container background: \#252525**  
* **Tertiary/boxes: \#2d2d2d**

**Text:**

* **Primary text: \#e8e8e8**  
* **Secondary text: \#d0d0d0 (NOT \#b0b0b0 \- too faded)**  
* **Accent gold (headers): \#d4af37**  
* **Accent bronze: \#cd7f32**

**Narration:**

* **Read-aloud: \#4fc3f7 (bright cyan) \- italicized, left-bordered box**  
* **Regular narration: \#c5d9e8 (NOT \#90a4ae \- too faded)**

**NPC Dialogue Colors (all bright, saturated):**

**Assign each NPC a unique, bright color. Use class names based on the NPC name (lowercase, hyphens for spaces).**

**Example color palette to draw from:**

* **\#7fff00  \- lime green**  
* **\#bb86fc  \- purple**  
* **\#ff9800  \- warm orange**  
* **\#f44336  \- red**  
* **\#ef5350  \- lighter red**  
* **\#a0bec8  \- bright steel blue**  
* **\#f48fb1  \- bright pink**  
* **\#ffcc80  \- bright peach**  
* **\#ffd54f  \- warm yellow**  
* **\#80deea  \- cyan**  
* **\#69f0ae  \- mint green**  
* **\#ffd740  \- amber**  
* **\#e040fb  \- magenta**  
* **\#40c4ff  \- sky blue**  
* **\#b388ff  \- lavender**  
* **\#ff8a80  \- salmon**  
* **\#ccff90  \- lime**  
* **\#84ffff  \- aqua**  
* **\#ce93d8  \- light purple**  
* **\#64b5f6  \- soft blue**


**Generic roles can use consistent colors across campaigns:**

* **Guards/soldiers: reds (\#f44336, \#ef5350)**  
* **Villains/antagonists: purples (\#bb86fc, \#ce93d8)**  
* **Friendly NPCs: greens/yellows (\#7fff00, \#ffd54f)**  
* **Mysterious figures: blues (\#80deea, \#64b5f6)**

**Add new NPCs as needed with bright, distinct colors. Never use:**

* **Anything below \#808080 brightness**  
* **Colors that blend with the background**  
* **Colors too similar to existing NPCs**

**Special Boxes:**

* **DM Notes: Background \#3d2c1f, border \#ff8a65, text \#ffcc80**  
* **Skill Checks: Background \#1e3a5f, border \#64b5f6, DC badge background \#64b5f6**  
* **Combat: Background \#3d1f1f, border \#ef5350**  
* **Options: Background \#2d2d2d, border \#546e7a, title \#80cbc4**  
  * **Risk text: \#ef9a9a**  
  * **Benefit text: \#a5d6a7**  
  * **Required text: \#90caf9**

  ---

  ## **HTML TEMPLATE STRUCTURE**

* **\<\!DOCTYPE html\>**  
* **\<html lang="en"\>**  
* **\<head\>**  
*     **\<meta charset="UTF-8"\>**  
*     **\<meta name="viewport" content="width=device-width, initial-scale=1.0"\>**  
*     **\<title\>Session \[NUMBER\]: \[TITLE\]\</title\>**  
*     **\<style\>**  
*         **/\* \=== BASE STYLES \=== \*/**  
*         **\* { box-sizing: border-box; margin: 0; padding: 0; }**  
*         **html { scroll-behavior: smooth; }**  
*           
*         **body {**  
*             **background-color: \#1a1a1a;**  
*             **color: \#e8e8e8;**  
*             **font-family: Arial, Verdana, sans-serif;**  
*             **font-size: 14px;**  
*             **line-height: 1.7;**  
*             **padding: 20px;**  
*         **}**  
*   
*         **.container {**  
*             **max-width: 900px;**  
*             **margin: 0 auto;**  
*             **padding: 40px;**  
*             **background-color: \#252525;**  
*             **border-radius: 8px;**  
*             **box-shadow: 0 4px 20px rgba(0,0,0,0.5);**  
*         **}**  
*   
*         **/\* \=== TITLE SECTION \=== \*/**  
*         **.title-section {**  
*             **text-align: center;**  
*             **padding: 40px 0 60px;**  
*             **border-bottom: 2px solid \#d4af37;**  
*             **margin-bottom: 40px;**  
*         **}**  
*   
*         **.session-number {**  
*             **font-size: 3.5em;**  
*             **font-weight: 700;**  
*             **color: \#d4af37;**  
*             **text-shadow: 2px 2px 4px rgba(0,0,0,0.5);**  
*             **letter-spacing: 4px;**  
*         **}**  
*   
*         **.session-title {**  
*             **font-size: 2em;**  
*             **color: \#e8e8e8;**  
*             **margin-top: 10px;**  
*             **letter-spacing: 2px;**  
*         **}**  
*   
*         **.session-date {**  
*             **font-size: 1.1em;**  
*             **color: \#d0d0d0;**  
*             **margin-top: 20px;**  
*         **}**  
*   
*         **.session-level {**  
*             **font-size: 1em;**  
*             **color: \#cd7f32;**  
*             **margin-top: 8px;**  
*         **}**  
*   
*         **/\* \=== TABLE OF CONTENTS \=== \*/**  
*         **.toc {**  
*             **background-color: \#2d2d2d;**  
*             **border: 1px solid \#d4af37;**  
*             **border-radius: 8px;**  
*             **padding: 25px 35px;**  
*             **margin-bottom: 50px;**  
*         **}**  
*   
*         **.toc-title {**  
*             **font-size: 1.5em;**  
*             **color: \#d4af37;**  
*             **margin-bottom: 15px;**  
*             **text-align: center;**  
*         **}**  
*   
*         **.toc-list {**  
*             **list-style: none;**  
*             **columns: 2;**  
*             **column-gap: 40px;**  
*         **}**  
*   
*         **.toc-list li { margin-bottom: 8px; break-inside: avoid; }**  
*         **.toc-list a { color: \#d0d0d0; text-decoration: none; font-size: 0.95em; transition: color 0.2s; }**  
*         **.toc-list a:hover { color: \#d4af37; }**  
*         **.toc-part { color: \#d4af37 \!important; font-weight: 600; }**  
*   
*         **/\* \=== HEADINGS \=== \*/**  
*         **h1 {**  
*             **font-size: 2.2em;**  
*             **color: \#d4af37;**  
*             **margin: 60px 0 30px;**  
*             **padding-bottom: 15px;**  
*             **border-bottom: 2px solid \#cd7f32;**  
*         **}**  
*   
*         **h2 {**  
*             **font-size: 1.6em;**  
*             **color: \#cd7f32;**  
*             **margin: 40px 0 20px;**  
*         **}**  
*   
*         **h3 {**  
*             **font-size: 1.3em;**  
*             **color: \#d0d0d0;**  
*             **margin: 30px 0 15px;**  
*             **font-style: italic;**  
*         **}**  
*   
*         **.scene-location {**  
*             **text-align: center;**  
*             **color: \#d0d0d0;**  
*             **font-style: italic;**  
*             **margin: \-10px 0 25px;**  
*             **font-size: 1em;**  
*         **}**  
*   
*         **/\* \=== PARAGRAPHS \=== \*/**  
*         **p { margin-bottom: 18px; text-align: justify; }**  
*   
*         **/\* \=== READ ALOUD NARRATION \=== \*/**  
*         **.read-aloud {**  
*             **color: \#4fc3f7;**  
*             **font-style: italic;**  
*             **padding: 20px 25px;**  
*             **margin: 20px 0;**  
*             **background: linear-gradient(135deg, rgba(79, 195, 247, 0.1) 0%, rgba(79, 195, 247, 0.03) 100%);**  
*             **border-left: 4px solid \#4fc3f7;**  
*             **border-radius: 0 8px 8px 0;**  
*         **}**  
*   
*         **/\* \=== REGULAR NARRATION \=== \*/**  
*         **.narration { color: \#c5d9e8; }**  
*   
*         **/\* \=== DIALOGUE \=== \*/**  
*         **.dialogue { margin: 15px 0; padding-left: 20px; }**  
*         **.dialogue-speaker { font-weight: 600; margin-right: 8px; }**  
*         **.dialogue-text { font-style: italic; }**  
*   
*         **/\* NPC Colors \- add a rule for each NPC in your session \*/**  
*         **/\* Use lowercase names, hyphens for spaces: .npc-guard-captain, .npc-innkeeper, etc. \*/**  
*         **/\* Example rules \- replace with your actual NPCs: \*/**  
*         **.npc-example-friendly .dialogue-speaker, .npc-example-friendly .dialogue-text { color: \#7fff00; }**  
*         **.npc-example-villain .dialogue-speaker, .npc-example-villain .dialogue-text { color: \#bb86fc; }**  
*         **.npc-example-merchant .dialogue-speaker, .npc-example-merchant .dialogue-text { color: \#ff9800; }**  
*         **.npc-guard .dialogue-speaker, .npc-guard .dialogue-text { color: \#f44336; }**  
*         **.npc-guards .dialogue-speaker, .npc-guards .dialogue-text { color: \#ef5350; }**  
*         **.npc-generic .dialogue-speaker, .npc-generic .dialogue-text { color: \#80deea; }**  
*   
*         **/\* \=== DM NOTES \=== \*/**  
*         **.dm-note {**  
*             **background-color: \#3d2c1f;**  
*             **border: 2px solid \#ff8a65;**  
*             **border-radius: 8px;**  
*             **padding: 20px 25px;**  
*             **margin: 25px 0;**  
*         **}**  
*   
*         **.dm-note-header {**  
*             **font-size: 0.9em;**  
*             **color: \#ff8a65;**  
*             **font-weight: 700;**  
*             **margin-bottom: 10px;**  
*             **text-transform: uppercase;**  
*             **letter-spacing: 2px;**  
*         **}**  
*   
*         **.dm-note-content { color: \#ffcc80; font-size: 0.95em; }**  
*         **.dm-note-content p { margin-bottom: 10px; }**  
*         **.dm-note-content p:last-child { margin-bottom: 0; }**  
*   
*         **/\* \=== SKILL CHECKS \=== \*/**  
*         **.skill-check {**  
*             **background-color: \#1e3a5f;**  
*             **border: 2px solid \#64b5f6;**  
*             **border-radius: 8px;**  
*             **padding: 15px 20px;**  
*             **margin: 15px 0;**  
*         **}**  
*   
*         **.skill-check-item { display: flex; margin-bottom: 8px; color: \#e3f2fd; }**  
*         **.skill-check-item:last-child { margin-bottom: 0; }**  
*   
*         **.dc-badge {**  
*             **background-color: \#64b5f6;**  
*             **color: \#0d47a1;**  
*             **padding: 2px 10px;**  
*             **border-radius: 4px;**  
*             **font-weight: 700;**  
*             **font-size: 0.85em;**  
*             **margin-right: 12px;**  
*             **white-space: nowrap;**  
*         **}**  
*   
*         **/\* \=== COMBAT BOX \=== \*/**  
*         **.combat-box {**  
*             **background-color: \#3d1f1f;**  
*             **border: 2px solid \#ef5350;**  
*             **border-radius: 8px;**  
*             **padding: 20px 25px;**  
*             **margin: 25px 0;**  
*         **}**  
*   
*         **.combat-header {**  
*             **font-size: 1.1em;**  
*             **color: \#ef5350;**  
*             **font-weight: 700;**  
*             **margin-bottom: 15px;**  
*             **text-transform: uppercase;**  
*             **letter-spacing: 1px;**  
*         **}**  
*   
*         **.combat-content { color: \#ffcdd2; }**  
*   
*         **/\* \=== OPTION BOXES \=== \*/**  
*         **.option-box {**  
*             **background-color: \#2d2d2d;**  
*             **border: 1px solid \#546e7a;**  
*             **border-radius: 8px;**  
*             **padding: 20px 25px;**  
*             **margin: 20px 0;**  
*         **}**  
*   
*         **.option-title { font-size: 1.1em; color: \#80cbc4; margin-bottom: 12px; }**  
*         **.option-content { color: \#d0d0d0; font-size: 0.95em; }**  
*         **.option-list { list-style: none; padding-left: 15px; }**  
*         **.option-list li { position: relative; padding-left: 20px; margin-bottom: 6px; }**  
*         **.option-list li::before { content: "▸"; position: absolute; left: 0; color: \#80cbc4; }**  
*         **.option-list .risk { color: \#ef9a9a; }**  
*         **.option-list .benefit { color: \#a5d6a7; }**  
*         **.option-list .required { color: \#90caf9; }**  
*   
*         **/\* \=== DIVIDERS \=== \*/**  
*         **.section-divider {**  
*             **text-align: center;**  
*             **margin: 50px 0;**  
*             **color: \#d4af37;**  
*             **font-size: 1.5em;**  
*             **letter-spacing: 10px;**  
*         **}**  
*   
*         **.part-divider {**  
*             **height: 3px;**  
*             **background: linear-gradient(90deg, transparent, \#d4af37, transparent);**  
*             **margin: 60px 0;**  
*             **border: none;**  
*         **}**  
*   
*         **/\* \=== LISTS \=== \*/**  
*         **ul, ol { margin: 15px 0; padding-left: 30px; }**  
*         **li { margin-bottom: 8px; color: \#d0d0d0; }**  
*   
*         **/\* \=== SPECIAL TEXT \=== \*/**  
*         **.emphasis { color: \#d4af37; font-weight: 600; }**  
*         **.item-name { color: \#ce93d8; font-weight: 600; }**  
*         **.location-name { color: \#80deea; font-style: italic; }**  
*   
*         **/\* \=== DM NOTES SECTION (END) \=== \*/**  
*         **.dm-notes-section {**  
*             **background-color: \#2d2d2d;**  
*             **border: 2px solid \#cd7f32;**  
*             **border-radius: 8px;**  
*             **padding: 30px 35px;**  
*             **margin-top: 60px;**  
*         **}**  
*   
*         **.dm-notes-section h1 { margin-top: 0; border-bottom-color: \#cd7f32; }**  
*         **.dm-notes-section h2 { color: \#d4af37; font-size: 1.3em; margin-top: 30px; }**  
*         **.dm-notes-section ul { list-style: none; padding-left: 0; }**  
*         **.dm-notes-section li { padding-left: 25px; position: relative; }**  
*         **.dm-notes-section li::before { content: "◆"; position: absolute; left: 0; color: \#cd7f32; }**  
*   
*         **/\* \=== RESPONSIVE \=== \*/**  
*         **@media (max-width: 768px) {**  
*             **body { padding: 10px; }**  
*             **.container { padding: 20px; }**  
*             **.session-number { font-size: 2.5em; }**  
*             **.toc-list { columns: 1; }**  
*             **h1 { font-size: 1.8em; }**  
*         **}**  
*     **\</style\>**  
* **\</head\>**  
* **\<body\>**  
*     **\<div class="container"\>**  
*         **\<\!-- TITLE \--\>**  
*         **\<div class="title-section"\>**  
*             **\<div class="session-number"\>SESSION \[NUMBER\]\</div\>**  
*             **\<div class="session-title"\>\[Title Here\]\</div\>**  
*             **\<div class="session-date"\>Date: \[In-game date\], \[Year\] P.D.\</div\>**  
*             **\<div class="session-level"\>Party Level: \[X\]\</div\>**  
*         **\</div\>**  
*   
*         **\<\!-- TABLE OF CONTENTS \--\>**  
*         **\<nav class="toc"\>**  
*             **\<div class="toc-title"\>Table of Contents\</div\>**  
*             **\<ul class="toc-list"\>**  
*                 **\<li\>\<a href="\#part1" class="toc-part"\>Part I: \[Title\]\</a\>\</li\>**  
*                 **\<\!-- Add more parts/scenes \--\>**  
*             **\</ul\>**  
*         **\</nav\>**  
*   
*         **\<\!-- CONTENT SECTIONS \--\>**  
*         **\<section id="part1"\>**  
*             **\<h1\>Part I: \[Title\]\</h1\>**  
*             **\<p class="scene-location"\>Time/Location info here\</p\>**  
*   
*             **\<h2\>Scene 1: \[Scene Title\]\</h2\>**  
*   
*             **\<div class="read-aloud"\>**  
*                 **Read-aloud narration goes here. This is what you read directly to players.**  
*             **\</div\>**  
*   
*             **\<p class="narration"\>Regular narration and description goes here.\</p\>**  
*   
*             **\<div class="dialogue npc-example-friendly"\>**  
*                 **\<span class="dialogue-speaker"\>\[NPC Name\]:\</span\>**  
*                 **\<span class="dialogue-text"\>"Dialogue goes here in quotes."\</span\>**  
*             **\</div\>**  
*   
*             **\<div class="dm-note"\>**  
*                 **\<div class="dm-note-header"\>DM Note\</div\>**  
*                 **\<div class="dm-note-content"\>**  
*                     **\<p\>Instructions or reminders for the DM go here.\</p\>**  
*                 **\</div\>**  
*             **\</div\>**  
*   
*             **\<div class="skill-check"\>**  
*                 **\<div class="skill-check-item"\>**  
*                     **\<span class="dc-badge"\>Skill DC \#\#\</span\>**  
*                     **\<span\>Description of what happens on success.\</span\>**  
*                 **\</div\>**  
*             **\</div\>**  
*   
*             **\<div class="option-box"\>**  
*                 **\<div class="option-title"\>Option Title\</div\>**  
*                 **\<div class="option-content"\>**  
*                     **\<p\>Description\</p\>**  
*                     **\<ul class="option-list"\>**  
*                         **\<li class="risk"\>\<strong\>Risk:\</strong\> What could go wrong\</li\>**  
*                         **\<li class="benefit"\>\<strong\>Benefit:\</strong\> What they gain\</li\>**  
*                         **\<li class="required"\>\<strong\>Required:\</strong\> What checks/abilities needed\</li\>**  
*                     **\</ul\>**  
*                 **\</div\>**  
*             **\</div\>**  
*         **\</section\>**  
*   
*         **\<hr class="part-divider"\>**  
*   
*         **\<\!-- MORE SECTIONS... \--\>**  
*   
*         **\<\!-- SESSION END \--\>**  
*         **\<section id="session-end"\>**  
*             **\<h1\>Session End\</h1\>**  
*             **\<div class="read-aloud"\>Closing narration / cliffhanger\</div\>**  
*             **\<div class="section-divider"\>⬥ ⬥ ⬥\</div\>**  
*         **\</section\>**  
*   
*         **\<\!-- DM NOTES SECTION \--\>**  
*         **\<section id="dm-notes" class="dm-notes-section"\>**  
*             **\<h1\>DM Notes\</h1\>**  
*               
*             **\<h2\>Session Summary\</h2\>**  
*             **\<p\>\<strong\>Date:\</strong\> \[In-game date\]\</p\>**  
*             **\<p\>\<strong\>Party Level:\</strong\> \[X\]\</p\>**  
*   
*             **\<h2\>Items Acquired\</h2\>**  
*             **\<ul\>**  
*                 **\<li\>Item 1\</li\>**  
*             **\</ul\>**  
*   
*             **\<h2\>Key Revelations\</h2\>**  
*             **\<ul\>**  
*                 **\<li\>Revelation 1\</li\>**  
*             **\</ul\>**  
*   
*             **\<h2\>NPCs Encountered\</h2\>**  
*             **\<ul\>**  
*                 **\<li\>NPC 1\</li\>**  
*             **\</ul\>**  
*   
*             **\<h2\>Consequences & Future Hooks\</h2\>**  
*             **\<ul\>**  
*                 **\<li\>Hook 1\</li\>**  
*             **\</ul\>**  
*   
*             **\<h2\>Next Session\</h2\>**  
*             **\<ul\>**  
*                 **\<li\>Setup for next session\</li\>**  
*             **\</ul\>**  
*         **\</section\>**  
*   
*         **\<div class="section-divider" style="margin-top: 60px;"\>⬥ END OF SESSION ⬥\</div\>**  
*     **\</div\>**  
* **\</body\>**  
* **\</html\>**  
    
  ---

  ## **NPC COLOR ASSIGNMENT**

**For each session, add CSS rules for every speaking NPC:**

* **.npc-\[name\] .dialogue-speaker, .npc-\[name\] .dialogue-text { color: \#\[BRIGHT\_COLOR\]; }**


**Naming convention:**

* **Lowercase**  
* **Hyphens for spaces: npc-guard-captain, npc-old-woman**  
* **Keep it short: npc-merchant, npc-innkeeper**

**Rules:**

* **Every NPC gets a unique color**  
* **Colors must be bright (nothing below \#808080)**  
* **Don't reuse colors within the same session**  
* **Generic roles (guards, villagers) can share colors**  
  ---

  ## **USAGE EXAMPLE**

**When I give you session content like:**

**"Create Session 5 \- The party arrives at the village and meets the innkeeper. They discover something is wrong with the local mine..."**

**You will:**

1. **Create the full HTML document using this template**  
2. **Format all narration, dialogue, DM notes, and skill checks appropriately**  
3. **Color-code all NPC dialogue (assigning unique colors to each NPC)**  
4. **Include a complete Table of Contents**  
5. **Add a DM Notes section at the end**  
6. **Save as Session\_\[NUMBER\]\_\[Title\].html**  
7. **Present the file to me**  
   ---

   ## **REMEMBER**

* **All colors must be bright and readable on dark background**  
* **Use Arial/Verdana at 14px base**  
* **Every NPC gets their own unique color**  
* **Structure content into clear Parts and Scenes**  
* **Include skill check DCs in highlighted badges**  
* **DM Notes are always boxed separately**  
* **NEVER use em-dashes (—) \- always use regular dashes (-) instead**  
* 

Custom Feat Creation: Output Format  
Used every 4 levels per group across all campaigns. Each feat is designed uniquely for the player it's for. The output format below is locked and applies to every feat.

Design phase  
Mechanics first, name last. Build the feat conversationally with the DM. The DM drives concept (character origin, story beats earned in play, mechanical itch the player has). Claude helps shape mechanics, iterate, balance. Name the feat once mechanics are locked.  
Common patterns used previously, reusable as starting points:

Resource pool size: 2 × proficiency bonus  
Resource refresh: Long Rest standard, Short Rest for some  
Save DC: 8 \+ proficiency \+ relevant ability mod  
d20 gamble: threshold (10+, 15+) for big effect, below threshold takes self-damage  
d10 effect table: for horror, chaos, or randomized phrase-based feats  
Dual competing dice: two dice rolled, higher determines branch, tie triggers a third option  
ASI: usually the relevant primary stat (+1), sometimes "any ability \+1"

Output phase: always deliver BOTH versions  
Once the feat is locked, produce two outputs.  
Version 1: D\&D Beyond Colored (full description)  
HTML for pasting into D\&D Beyond's description editor. All rules text, inline color spans, long-form. This is the canonical description.  
Critical: paste into the HTML/Source view, NOT the WYSIWYG view. The rich-text editor strips inline style attributes on save when pasted via WYSIWYG. Source view preserves them.  
Version 2: Snippet (condensed)  
For the snippet field on D\&D Beyond and at-the-table quick reference. Densely bolded, bullet dots (•) at the start of options, terse phrasing, key numbers always bolded.

Color scheme  
Apply via inline span: \<span style="color: \#HEX;"\>text\</span\>  
ElementHexDamage\#ff6666 (red)Saves\#66b3ff (blue)Conditions (Frightened, Restrained, etc.)\#ffaa00 (orange)Healing\#66cc66 (green)  
Character-specific palettes are permitted when thematic. Lock them on first appearance of the feat. Examples used previously:

Thread-themed: gold \#daa520, bright gold \#ffd700  
Horror / whisper: red whispers, light pink phrases

Choose character-specific colors that mean something to who the character is.

HTML tags D\&D Beyond accepts

\<strong\>: bold  
\<em\>: italic  
\<p\>: paragraph  
\<h2\>: header  
\<span style="color: \#HEX;"\>: inline color  
\<ul\>, \<li\>: lists (use in full version; snippets use • manually)

Template: Version 1, Full Description (Colored)  
html\<h2\>\<strong\>\[FEAT NAME\]\</strong\>\</h2\>

\<p\>\<em\>Feat (Prerequisites: \[race\], \[class\])\</em\>\</p\>

\<p\>\[Flavor narrative, 1-3 sentences, setting the character's connection to this power.\] You gain the following benefits:\</p\>

\<p\>\<strong\>Ability Score Increase:\</strong\> Increase \[your X score / one ability score of your choice\] by \<strong\>1\</strong\>, to a maximum of \<strong\>20\</strong\>.\</p\>

\<p\>\<span style="color:\#\[CHAR\_COLOR\];"\>\<strong\>\[Resource Name\]:\</strong\>\</span\> You have \[resource\] equal to \<strong\>2 × your proficiency bonus\</strong\>. You regain all expended \[resource\] when you finish a \<strong\>Long Rest\</strong\>.\</p\>

\<p\>\<span style="color:\#\[CHAR\_COLOR\];"\>\<strong\>\[Feature Name\] (1 \[Resource\]):\</strong\>\</span\> \[Description with mechanics: \<strong\>2d6 \<span style="color:\#ff6666;"\>force damage\</span\>\</strong\>, \<span style="color:\#66b3ff;"\>\<strong\>Dexterity save\</strong\>\</span\>, \<span style="color:\#ffaa00;"\>\<strong\>Frightened\</strong\>\</span\> until end of next turn, etc.\]\</p\>

\<p\>\[Additional features as needed: secondary abilities, crafting addenda, scaling clauses, etc.\]\</p\>

Template: Version 2, Snippet (Condensed)  
\<em\>\[1-sentence italic flavor line.\]\</em\>

\<strong\>\[Resource Name\]:\</strong\> \<strong\>\[X\] points\</strong\> max. Regain \<strong\>\[Y\]\</strong\> on \<strong\>Long Rest\</strong\>.

\<strong\>\[Feature Name\]:\</strong\> On \[trigger\], choose one:  
\- \<strong\>\[Sub-option A\] (1 \[Resource\]):\</strong\> \+\<strong\>2d6 \<span style="color:\#ff6666;"\>force\</span\>\</strong\>.  
\- \<strong\>\[Sub-option B\] (2 \[Resource\]):\</strong\> Roll \<strong\>d20\</strong\>. \<strong\>10+:\</strong\> \+\<strong\>4d6 \<span style="color:\#ff6666;"\>force\</span\>\</strong\>. \<strong\>9-:\</strong\> No bonus, take \<strong\>1d6 \<span style="color:\#ff6666;"\>force\</span\>\</strong\>.  
\- \<strong\>\[Sub-option C\] (3 \[Resource\]):\</strong\> Roll \<strong\>d20\</strong\>. \<strong\>15+:\</strong\> \+\<strong\>6d6 \<span style="color:\#ff6666;"\>force\</span\>\</strong\>, push \<strong\>15 ft\</strong\>. \<strong\>14-:\</strong\> No bonus, take \<strong\>3d6 \<span style="color:\#ff6666;"\>force\</span\>\</strong\>, unusable until \<strong\>Action\</strong\> repair.

\<strong\>\[Additional Feature\]:\</strong\> \[Terse description with all key numbers bolded.\]

