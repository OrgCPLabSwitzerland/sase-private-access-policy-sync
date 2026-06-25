document.getElementById("btn").onclick = openModal;

let validationPassed = false;

async function validatePolicy() {

    const output = document.getElementById("output");
    const installBtn = document.getElementById("btn");

    try {
        output.innerText = "Validating policy...";

        const res = await fetch("https://172.31.100.201:5000/validate-policy");

        if (!res.ok) {
            throw new Error("HTTP " + res.status);
        }

        const data = await res.json();

        // trust backend result
        if (data.status === "valid") {

            validationPassed = true;
            installBtn.disabled = false;

            output.innerHTML = `
                ✅ Validation passed.<br>
                You can now install the policy.
            `;

        } else {

            validationPassed = false;
            installBtn.disabled = true;

            output.innerHTML = `
                <div class="validation-error">
                    ❌ Validation failed
                </div>

                <div class="validation-hint">
                    Only host or network objects using IP or CIDR notation are supported.
                </div>

                <ul>
                    ${data.errors.map(e => `<li>${e}</li>`).join("")}
                </ul>
            `;
        }

    } catch (err) {
        output.innerText = "ERROR: " + err;
    }
}

function openModal() {

    const select = document.getElementById("networkSelect");
    const selectedText = select.options[select.selectedIndex].text;

    document.getElementById("networkInfo").innerText =
        "Target Network: " + selectedText;

    document.getElementById("confirmModal").style.display = "block";
}

function closeModal() {
    document.getElementById("confirmModal").style.display = "none";
}


function confirmInstall() {

    const select = document.getElementById("networkSelect");
    const networkId = select.value;

    closeModal();
    installPolicy(networkId);
}

async function installPolicy(networkId) {

    console.log("validationPassed:", validationPassed);

    if (!validationPassed) {
        alert("Please validate the policy first.");
        return;
    }

    const btn = document.getElementById("btn");
    const output = document.getElementById("output");

    btn.disabled = true;

    try {
        output.innerText = "Installing policy...";

        const res = await fetch(`https://172.31.100.201:5000/install-policy?network_id=${networkId}`);

        if (!res.ok) {
            throw new Error("HTTP " + res.status);
        }

        const data = await res.json();

        console.log("BACKEND:", data);

        renderOutput(data);

    } catch (err) {
        console.error(err);
        output.innerText = "ERROR: " + err;
    } finally {
        btn.disabled = false;

        validationPassed = false;

        document.getElementById("btn").disabled = true;

        const output = document.getElementById("output");


        output.innerHTML += `
            <br><br>
            <div style="color:#888; font-size:12px;">
            Please validate again before the next install.
        </div>
    `;
    }
}

async function loadNetworks() {

    const output = document.getElementById("output");

    try {
        const res = await fetch("https://172.31.100.201:5000/get-networks");
        const data = await res.json();

        if (data.status !== "success") {
            output.innerText = "Error: " + data.message;
            return;
        }

        let html = `
            <table>
                <tr>
                    <th>Name</th>
                    <th>ID</th>
                </tr>
        `;

        // fill dropdown
        const select = document.getElementById("networkSelect");
        select.innerHTML = "";

        data.networks.forEach(n => {

            const option = document.createElement("option");
            option.value = n.id;
            option.text = `${n.name} (${n.type})`;
            select.appendChild(option);

            html += `
                <tr>
                    <td>${n.name} (${n.type})</td>
                    <td>${n.id}</td>
                </tr>
            `;
        });

        html += "</table>";


    } catch (err) {
        output.innerText = "ERROR: " + err;
    }
}

window.onload = loadNetworks;

