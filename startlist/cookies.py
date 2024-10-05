cookies = """

function cookieName(cname) {
    const pagePath = window.location.pathname;  // Get the current page path
    const trimmed = pagePath.replace(/^.*\/(.*)-startlist.html$/, '$1');
    const fullCookieName = trimmed + "_" + cname;  // Add page path to cookie name
    console.log('cookieName: pagePath:', pagePath, 'trimmed:', trimmed);
    return fullCookieName;
}

function setCookie(cname, cvalue, exdays) {
    /*
    const pagePath = window.location.pathname;  // Get the current page path
    const fullCookieName = pagePath + "_" + cname;  // Add page path to cookie name
    */
    const fullCookieName = cookieName(cname);
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    const cookie = fullCookieName + "=" + cvalue + ";" + expires + ";path=/";
    console.log('setCookie: set cookie:', cookie);
    document.cookie = cookie;
}
function getCookie(cname) {
    /*
    const pagePath = window.location.pathname;  // Get the current page path
    const fullCookieName = pagePath + "_" + cname;  // Add page path to cookie name
    */
    const fullCookieName = cookieName(cname);
    let name = fullCookieName + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    console.log('getCookie: decoded cookie:', decodedCookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            console.log('getCookie: %s: %s', cname, c.substring(name.length, c.length));
            return c.substring(name.length, c.length);
        }
    }
    console.log('getCookie: %s: null', cname);
    return "";
}
"""
