function renderOutput(data) {

    const output = document.getElementById("output");

    if (data.status === "success") {

        window.objectMap = data.object_map || {};

        let html = `
            <div style="margin-bottom: 10px; font-weight: bold;">
                ✅ Policy pushed successfully (${data.rules_sent} rules)
            </div>
        `;

        if (data.rules && data.rules.length > 0) {
            html += renderTable(data.rules);
        } else {
            html += "<div>No rules returned from backend</div>";
        }

        output.innerHTML = html;
        return;
    }

    output.innerText = JSON.stringify(data, null, 2);
}


function renderTable(rules) {

    let html = `
        <table>
            <tr>
                <th>Name</th>
                <th>Sources</th>
                <th>Destinations</th>
                <th>Services</th>
                <th>Action</th>
                <th>Warnings</th>
            </tr>
    `;

    rules.forEach(rule => {

        html += `
            <tr>
                <td>${rule.name || ""}</td>
                <td>${window.format(rule.sources)}</td>
                <td>${window.format(rule.destinations)}</td>
                <td>${window.format(rule.services)}</td>
                <td>${rule.allowed ? "Allow" : "Deny"}</td>
                <td class="warning">${window.detectWarnings(rule)}</td>
            </tr>
        `;
    });

    html += "</table>";

    return html;
}
