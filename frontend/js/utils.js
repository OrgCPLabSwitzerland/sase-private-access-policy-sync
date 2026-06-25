window.format = function (val) {

    if (!val) return "Any";

    // services (array)
    if (Array.isArray(val)) {
        return val
            .map(s => s.replace(/_cp-[^, ]+$/, ""))  // strip SASE suffix
            .join(", ");
    }

    // objects (sources / destinations)
    if (typeof val === "object") {

        if (val.any) return "Any";

        if (val.addresses && val.addresses.length > 0) {
            return val.addresses
                .map(id => window.objectMap && window.objectMap[id] ? window.objectMap[id] : id)
                .join(", ");
        }

        if (Object.keys(val).length === 0) {
            return "Any";
        }
    }

    return val;
};

window.detectWarnings = function (rule) {

    let warnings = [];

    if (!rule.sources || Object.keys(rule.sources).length === 0) {
        warnings.push("empty source");
    }

    if (!rule.destinations || Object.keys(rule.destinations).length === 0) {
        warnings.push("ANY destination");
    }

    return warnings.join(" ⚠ ");
};

window.isValidAddress = function(obj) {

    if (!obj) return true;

    // ANY allowed
    if (obj.any) return true;

    // empty = ANY
    if (Object.keys(obj).length === 0) return true;

    if (obj.addresses && Array.isArray(obj.addresses)) {
        return obj.addresses.every(a => typeof a === "string" && a.length > 0);
    }

    return false;
};
