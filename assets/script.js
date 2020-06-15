console.log("Hi there! Feel to explore the code!");
//let apiURL = 'http://127.0.0.1:5000/api'
let apiURL = '/api'
let playersTableOriginal = $("#onlinePlayersTable").html()

let serverBusy = false

const statusMsg = (msg, apiServerBusy = false) => {
    if (apiServerBusy == false && serverBusy == false) {
        if (msg == "off") {
            $("#serverStatus").text("Offline")
            $("#serverStatus").addClass("text-danger")
            $("#serverStatus").removeClass("text-success text-warning text-info")
            $("#msg h5").text("Server is offline");
            $("#msg").collapse('show')
        } else if (msg == "shutdown") {
            $("#serverStatus").text("Shutting Down")
            $("#serverStatus").addClass("text-danger")
            $("#serverStatus").removeClass("text-success text-warning text-info")
            $("#msg h5").text("Server is shutting down");
            $("#msg").collapse('hide')
        } else if (msg == "starting") {
            $("#serverStatus").text("Starting")
            $("#serverStatus").addClass("text-warning")
            $("#serverStatus").removeClass("text-success text-danger text-info")
            $("#msg h5").text("Server is getting ready");
            $("#msg").collapse('show')
        } else if (msg == "saving") {
            $("#serverStatus").text("Saving")
            $("#serverStatus").addClass("text-info")
            $("#serverStatus").removeClass("text-danger text-warning text-success")
            $("#msg h5").text("Server is saving");
            $("#msg").collapse('hide')
        } else if (msg == "reboot") {
            $("#serverStatus").text("Rebooting")
            $("#serverStatus").addClass("text-info")
            $("#serverStatus").removeClass("text-danger text-warning text-success")
            $("#msg h5").text("Server is rebooting");
            $("#msg").collapse('hide')
        } else if (msg == "ready") {
            $("#serverStatus").text("Ready")
            $("#serverStatus").addClass("text-success")
            $("#serverStatus").removeClass("text-danger text-warning text-info")
            $("#msg h5").text("Server is ready");
            $("#msg").collapse('hide')
        }
    }
}

const init = async () => {
    try {
        let res = await fetch(apiURL);
        const data = await res.json();

        //console.log(data);
        statusMsg(data.status, data.busy)
        s = data.settings;
        console.log(data.logs)
        let sLogs = data.logs.split(/\r?\n/)
        sLogs.reverse()
        $("#consoleText").html("")
        sLogs.forEach((m) => {
            let row = document.createElement("div");
            row.innerText = m;
            $("#consoleText").append(row);
        });


        $("#titleIP").html(`${s.PublicIP}:${s.Port}`);

        $("#serverName").html(s.ServerName);
        $("#owner").html(s.OwnerName);
        $("#maxFramerate").html(parseFloat(s.MaxServerFramerate));

        $("#maxPlayers").html(s.MaximumPlayerCount);
        $("#onlinePlayersTable").html(playersTableOriginal);
        $("#offlinePlayersTable").html(playersTableOriginal);
        if (data.players.hasOwnProperty('playerInfo')) {
            $("#onlinePlayers").text(data.players.playerInfo.filter(
                (p) => p.inGame
            ).length);

            if (data.players) {
                data.players.playerInfo.forEach((p) => {
                    let row = document.createElement("tr");
                    row.innerHTML = `<td>${p.playerName}</td>
                    <td>${p.playerCategory}</td>
                    <td>${p.inGame}</td>`;
                    if (p.inGame == true) {
                        $("#onlinePlayersTable>tbody").append(row);
                    } else if (p.playerName != '') {
                        $("#offlinePlayersTable>tbody").append(row);

                    }
                });
            }
        }
    } catch (e) {
        console.log(e)
        $("#msg h5").text("ERROR! Try again in 10s");
        $("#msg").collapse('show');
        serverBusy = false;
        statusMsg("off");
    }
};
setInterval(init, 1000);
init()
$("#saveGameBtn").click(function (e) {
    e.preventDefault();
    statusMsg("saving")
    serverBusy = true
    $.ajax({
        type: "POST",
        url: apiURL + "/savegame",
        dataType: 'json',
        success: function (result) {
            setTimeout(() => { serverBusy = false }, 2000)
        },
        error: function (result) {
            console.log(result)
            alert('Error');
        }
    });
});
$("#rebootServerBtn").click(function (e) {
    e.preventDefault();
    statusMsg("reboot")
    serverBusy = true
    $.ajax({
        type: "POST",
        url: apiURL + "/reboot",
        dataType: 'json',
        success: function (result) {
            setTimeout(() => { serverBusy = false }, 2000)
        },
        error: function (result) {
            console.log(result)
            alert('Error');
        }
    });
});
$("#stopLauncherBtn").click(function (e) {
    e.preventDefault();
    statusMsg("shutdown")
    serverBusy = true
    setTimeout(() => { serverBusy = false; statusMsg("off") }, 2000)
    $.ajax({
        type: "POST",
        url: apiURL + "/shutdown",
        dataType: 'json',
        success: function (result) {
        },
        error: function (result) {
            console.log(result)
        }
    });
});