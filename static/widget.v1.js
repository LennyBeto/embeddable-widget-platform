(function () {
  "use strict";

  // The loader finds its own <script> tag to read the widget id and figure out
  // which origin the API lives on — the same trick every real embed script uses.
  var scripts = document.getElementsByTagName("script");
  var thisScript = scripts[scripts.length - 1];
  var scriptUrl = new URL(thisScript.src);
  var API_ORIGIN = scriptUrl.origin;
  var widgetId = scriptUrl.searchParams.get("id");

  if (!widgetId) {
    console.error("[widget] missing ?id= on the embed <script> tag");
    return;
  }

  function renderWidget(config) {
    var container = document.createElement("div");
    container.className = "wcp-widget";
    container.style.cssText =
      "max-width:360px;padding:16px;border:1px solid #ddd;border-radius:8px;font-family:sans-serif;";

    var title = document.createElement("h3");
    title.textContent = config.title;
    container.appendChild(title);

    if (config.description) {
      var desc = document.createElement("p");
      desc.textContent = config.description;
      desc.style.cssText = "font-size:14px;color:#555;";
      container.appendChild(desc);
    }

    var form = document.createElement("form");

    config.fields.forEach(function (field) {
      var label = document.createElement("label");
      label.textContent = field.label;
      label.style.cssText = "display:block;margin-top:8px;font-size:13px;";

      var input = document.createElement(field.field_type === "textarea" ? "textarea" : "input");
      if (field.field_type !== "textarea") {
        input.type = field.field_type === "email" ? "email" : "text";
      }
      input.name = field.name;
      input.required = !!field.required;
      input.style.cssText = "display:block;width:100%;padding:6px;margin-top:2px;box-sizing:border-box;";

      label.appendChild(input);
      form.appendChild(label);
    });

    // Honeypot: visually hidden (not display:none, which some bots skip), off-screen,
    // no label — a human never encounters it, a naive bot filling every input will.
    var honeypot = document.createElement("input");
    honeypot.type = "text";
    honeypot.name = "hp_field";
    honeypot.tabIndex = -1;
    honeypot.autocomplete = "off";
    honeypot.style.cssText = "position:absolute;left:-9999px;width:1px;height:1px;opacity:0;";
    form.appendChild(honeypot);

    var submitBtn = document.createElement("button");
    submitBtn.type = "submit";
    submitBtn.textContent = config.button_text || "Submit";
    submitBtn.style.cssText = "margin-top:10px;padding:8px 16px;";
    form.appendChild(submitBtn);

    var statusMsg = document.createElement("p");
    statusMsg.style.cssText = "font-size:13px;margin-top:8px;";
    container.appendChild(form);
    container.appendChild(statusMsg);

    form.addEventListener("submit", function (evt) {
      evt.preventDefault();
      var formData = new FormData(form);
      var data = {};
      formData.forEach(function (value, key) {
        if (key !== "hp_field") data[key] = value;
      });

      fetch(API_ORIGIN + "/widgets/" + widgetId + "/submissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: data, hp_field: formData.get("hp_field") || "" }),
      })
        .then(function (res) {
          if (!res.ok) throw new Error("submission failed");
          statusMsg.textContent = "Thanks! Your submission was received.";
          statusMsg.style.color = "green";
          form.reset();
        })
        .catch(function () {
          statusMsg.textContent = "Something went wrong. Please try again.";
          statusMsg.style.color = "red";
        });
    });

    thisScript.parentNode.insertBefore(container, thisScript.nextSibling);
  }

  fetch(API_ORIGIN + "/widgets/" + widgetId + "/config")
    .then(function (res) {
      if (!res.ok) throw new Error("config fetch failed");
      return res.json();
    })
    .then(renderWidget)
    .catch(function (err) {
      console.error("[widget] failed to load:", err);
    });
})();
