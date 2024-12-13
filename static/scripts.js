function getDeviceInfo() {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    let device = "E panjohur";
    let browser = "E panjohur";

    // Përcakto pajisjen
    if (/android/i.test(userAgent)) {
        device = "Android";
    } else if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
        device = "iOS";
    } else if (/Windows/.test(userAgent)) {
        device = "Windows";
    } else if (/Macintosh/.test(userAgent)) {
        device = "Mac";
    }

    // Përcakto shfletuesin
    if (/Chrome/.test(userAgent)) {
        browser = "Chrome";
    } else if (/Firefox/.test(userAgent)) {
        browser = "Firefox";
    } else if (/Safari/.test(userAgent)) {
        browser = "Safari";
    } else if (/Edge/.test(userAgent)) {
        browser = "Edge";
    } else if (/MSIE|Trident/.test(userAgent)) {
        browser = "Internet Explorer";
    }

    return {
        device: device,
        browser: browser,
        platform: navigator.platform || "E panjohur"
    };
}

function getLocation(callback) {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                callback({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                });
            },
            (error) => {
                console.error("Gabim gjatë marrjes së lokacionit:", error);
                callback(null); // Nëse dështoi Geolocation
            }
        );
    } else {
        console.warn("Geolocation nuk është i mbështetur në këtë pajisje.");
        callback(null);
    }
}

function collectFullClientInfo() {
    const deviceInfo = getDeviceInfo();
    const screenSize = {
        width: window.screen.width,
        height: window.screen.height
    };
    const language = navigator.language || "E panjohur";
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || "E panjohur";

    getLocation((location) => {
        const clientInfo = {
            time: new Date().toISOString(),
            ip: "Do të merret nga serveri", // IP do të vendoset nga serveri
            device: deviceInfo.device,
            browser: deviceInfo.browser,
            platform: deviceInfo.platform,
            screenSize: screenSize,
            language: language,
            timeZone: timeZone,
            location: location || "E panjohur" // Nëse lokacioni dështoi
        };

        console.log("Informacioni i plotë i klientit:", clientInfo);

        // Dërgo të dhënat te serveri për ruajtje
        fetch('/api/save_client_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(clientInfo)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Gabim HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Të dhënat u ruajtën me sukses:", data);
        })
        .catch(error => {
            console.error("Gabim gjatë ruajtjes së të dhënave:", error);
        });
    });
}

// Thirr funksionin për mbledhjen e të dhënave
collectFullClientInfo();
