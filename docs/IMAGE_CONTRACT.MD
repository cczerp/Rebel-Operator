🚨 FILE UPLOAD NON-NEGOTIABLES (Button Does Nothing)
1️⃣ There MUST be a real <input type="file">

No exceptions.
No file input = no file picker.

<input type="file" id="photoInput" />


A <button> alone cannot open saved images.

2️⃣ The button MUST trigger .click() on the file input

The file picker only opens if the button directly triggers the input.

document.getElementById("photoInput").click();


If this is missing, nothing happens. Period.

3️⃣ The trigger MUST be inside a direct user action

The .click() call must happen:

Inside an onclick

Or inside a click event listener

✅ Allowed
<button onclick="openPicker()">Upload</button>

❌ Blocked silently

setTimeout

async / await

useEffect

Page load

Background JS

If it’s not immediately tied to a click, the browser blocks it.

4️⃣ The file input CANNOT be display: none

This one kills functionality silently.

❌ Breaks picker
input[type="file"] {
  display: none;
}

✅ Allowed
opacity: 0;
position: absolute;
left: -9999px;


Hidden is fine. Removed from layout is not.

5️⃣ The file input MUST exist in the DOM at click time

If React, Vue, or JS conditionally renders it, the click fails.

❌ Broken
{showUploader && <input type="file" />}

✅ Required

Render it always, hide it visually.

6️⃣ The file input MUST NOT be disabled

Even temporarily.

<input type="file" disabled />


One disabled=true during loading = dead button.

7️⃣ The handler function MUST exist (no ghost functions)

If your input has:

<input onchange="handlePhotoSelect(event)" />


Then this MUST exist globally:

function handlePhotoSelect(e) {}


Missing handler can cause silent failure.

8️⃣ accept MUST NOT filter everything out

If you filter wrong, picker opens empty or not at all.

❌ Over-filtered
accept="image/jpg"

✅ Safe
accept="image/*"

9️⃣ HTTPS is REQUIRED for consistent behavior

File pickers behave inconsistently on HTTP.

Render = ✅ good

Local dev on HTTP = 🚨 risk

🔟 The picker NEVER shows server images

This is a hard rule.

The file picker only shows:

Local device files

Downloads

Camera roll

It will never show:

S3 images

Database images

Previously uploaded photos

Those require a custom gallery UI, not the file picker.

✅ Canonical “This Must Work” Pattern

If this exact structure doesn’t open the picker, something external is broken.

<input
  type="file"
  id="photoInput"
  accept="image/*"
  style="opacity:0; position:absolute; left:-9999px;"
  onchange="handlePhotoSelect(event)"
/>

<button onclick="openPicker()">Upload</button>

<script>
function openPicker() {
  document.getElementById("photoInput").click();
}

function handlePhotoSelect(e) {
  console.log(e.target.files);
}
</script>
