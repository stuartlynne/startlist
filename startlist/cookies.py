cookies = """
function setCookie(cname, cvalue, exdays) {
    console.log('setCookie: cname:', cname);
    const d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires=" + d.toUTCString();
    //cookie = "lastSelectedCell=" + cvalue + ";" + expires + ";path=/";
    cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
    console.log('setCookie: set cookie:', cookie);
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
    let decodedCookie = decodeURIComponent(document.cookie);
    return "";
}
function getCookie(cname) {
    let name = cname + "=";
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
