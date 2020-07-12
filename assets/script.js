console.log("Hi there! Feel to explore the code!");
//let apiURL = 'http://127.0.0.1:80/api'
let apiURL = "/api";
let playersTableOriginal = $("#onlinePlayersTable").html();

let oldMsg = "";
let oldSettings = {};
let oldPlayers = {};
let isAdmin = false;

const statusMsg = (msg) => {
    if (oldMsg != msg) {
        oldMsg = msg;
        $("#serverStatus").removeClass(
            "text-success text-warning text-danger text-info"
        );
        if (msg == "off") {
            $("#serverStatus").text("Offline");
            $("#serverStatus").addClass("text-danger");
            $("#msg h5").text("Server is offline");
            $("#msg").collapse("show");
        } else if (msg == "shutdown") {
            $("#serverStatus").text("Shutting Down");
            $("#serverStatus").addClass("text-danger");
            $("#msg h5").text("Server is shutting down");
            $("#msg").collapse("hide");
        } else if (msg == "starting") {
            $("#serverStatus").text("Starting");
            $("#serverStatus").addClass("text-warning");
            $("#msg h5").text("Server is getting ready");
            $("#msg").collapse("show");
        } else if (msg == "saving") {
            $("#serverStatus").text("Saving");
            $("#serverStatus").addClass("text-info");
            $("#msg h5").text("Server is saving");
            $("#msg").collapse("hide");
        } else if (msg == "reboot") {
            $("#serverStatus").text("Rebooting");
            $("#serverStatus").addClass("text-info");
            $("#msg h5").text("Server is rebooting");
            $("#msg").collapse("hide");
        } else if (msg == "ready") {
            $("#serverStatus").text("Ready");
            $("#serverStatus").addClass("text-success");
            $("#msg h5").text("Server is ready");
            $("#msg").collapse("hide");
        }
    }
};
const compareObj = (obj1, obj2) => {
    return JSON.stringify(obj1) === JSON.stringify(obj2);
};

let logList = [];
const tick = async () => {
    try {
        let res = await fetch(apiURL);
        const data = await res.json();
        // console.log(data);

        if (data.hasUpdate != false) {
            let ghLink = document.querySelector("#githubLink");
            let tipInstance = ghLink._tippy;
            tipInstance.setContent("Update Available: " + data.hasUpdate);
            tipInstance.show();
        }
        statusMsg(data.status);
        isAdmin = data.admin;
        if ($("#console").length && !isAdmin) {
            location.reload();
        }
        // smart scroll
        if (isAdmin) {
            let log = $("#consoleText")[0];
            let isBottom = log.scrollTop == log.scrollHeight - log.clientHeight;

            let sLogs = data.logs.split(/\r?\n/);
            //$("#consoleText").html("");
            let newLogs = sLogs.filter((i) => !logList.includes(i) && i != "");

            newLogs.forEach((entry) => {
                logList.push(entry);

                let content = "";
                let levelType = "";
                entry = entry.replace(/"|'/g, "");
                entry = linkify(entry);

                if (entry.includes("INFO")) {
                    levelType = "INFO";
                    let parts = entry.split("INFO");
                    content =
                        "<i class='fas fa-info-circle iconInfo'></i> " +
                        parts[0] +
                        //"<span style='color: green;'>INFO</span>" +
                        parts[1];
                } else if (entry.includes("WARNING")) {
                    let parts = entry.split("WARNING");
                    levelType = "WARNING";
                    content =
                        "<i class='fas fa-exclamation-triangle iconWarn'></i> " +
                        parts[0] +
                        //"<span style='color: red;'>WARNING</span>" +
                        parts[1];
                } else {
                    content = entry;
                }

                let row = document.createElement("div");
                row.innerHTML = content;
                if (levelType == "WARNING") {
                    $(row).addClass("warning");
                }

                $("#consoleText").append(row);
            });

            if (isBottom) log.scrollTop = log.scrollHeight - log.clientHeight;
        }

        s = data.settings;
        if (data.stats) {
            $("#hWL").html(data.stats.isEnforcingWhitelist.toString());
            $("#hPW").html(data.stats.hasServerPassword.toString());
            $("#hCM").html(data.stats.creativeMode.toString());

            $("#serverVersion").html(data.stats.build);
            $("#framerateStats").html(
                parseInt(data.stats.averageFPS) +
                    "/" +
                    parseInt(s.MaxServerFramerate) +
                    " FPS"
            );
        } else {
            if (
                data.status == "starting" ||
                data.status == "off" ||
                data.status == "shutdown"
            ) {
                $("#serverVersion").html("");
                $("#framerateStats").html("");
            }
        }
        if (!compareObj(oldSettings, s)) {
            oldSettings = s;

            $("#serverName").html(s.ServerName);
            $("#serverPort").html(`${s.PublicIP}:${s.Port}`);
            $("#owner").html(s.OwnerName);
        }
        if (
            data.status == "starting" ||
            data.status == "off" ||
            data.status == "shutdown"
        ) {
            $("#playersStats").text("");
        } else {
            if (!compareObj(oldPlayers, data.players)) {
                oldPlayers = data.players;
                $("#onlinePlayersTable").html(playersTableOriginal);
                $("#offlinePlayersTable").html(playersTableOriginal);
                if (data.players.hasOwnProperty("playerInfo")) {
                    $("#playersStats").text(
                        data.players.playerInfo.filter((p) => p.inGame).length +
                            "/" +
                            s.MaximumPlayerCount
                    );

                    if (data.players) {
                        data.players.playerInfo.forEach((p) => {
                            let row = document.createElement("tr");
                            row.innerHTML = `<td>${p.playerName}</td>
                            <td>${p.playerCategory}</td>
                            <td>${p.playerGuid}</td>`;

                            if (p.inGame == true) {
                                if (isAdmin) {
                                    row.innerHTML +=
                                        "<td>" +
                                        createActionButtons("online", p) +
                                        "</td>";
                                }
                                $("#onlinePlayersTable>tbody").append(row);
                            } else {
                                $("#offlinePlayersTable>tbody").append(row);
                                if (isAdmin) {
                                    row.innerHTML +=
                                        "<td>" +
                                        createActionButtons("offline", p) +
                                        "</td>";
                                }
                            }
                        });
                    }
                }
            }
        }
    } catch (e) {
        console.log(e);
        $("#msg h5").text("ERROR! Try again in 10s");
        $("#msg").collapse("show");
        statusMsg("off");
    }
};

setInterval(tick, 1000);
tick();

const createActionButtons = function (status, player) {
    dropDownDiv = $("<div/>").attr({ class: "btn-group dropup" });
    DDButton = $("<button/>")
        .attr({
            type: "button",
            class: "btn btn-secondary dropdown-toggle",
            "data-toggle": "dropdown",
            "aria-haspopup": "true",
            "aria-expanded": "false",
            id: "dropdownMenu2",
        })
        .text("Actions");
    DDMenu = $("<div/>").attr({
        class: "dropdown-menu",
        "aria-labelledby": "dropdownMenu2",
    });
    dropDownDiv.append(DDButton);
    dropDownDiv.append(DDMenu);
    sButton = $("<button/>").attr({
        type: "button",
        class: "dropdown-item pBtn p-1",
        "data-guid": player.playerGuid,
        "data-name": player.playerName,
    });

    actionButtonBufferList = [];
    if (player.playerCategory != "Owner") {
        kickButton = sButton.clone().attr("data-action", "kick").text("Kick");
        actionButtonBufferList.push(kickButton);

        banButton = sButton.clone().attr("data-action", "ban").text("Ban");
        actionButtonBufferList.push(banButton);

        WLButton = sButton.clone().attr("data-action", "WL").text("Whitelist");
        actionButtonBufferList.push(WLButton);

        AdminButton = sButton
            .clone()
            .attr("data-action", "admin")
            .text("Give Admin");
        actionButtonBufferList.push(AdminButton);

        ResetButton = sButton
            .clone()
            .attr("data-action", "reset")
            .text("Reset Perms");
        actionButtonBufferList.push(ResetButton);

        /*
        RemoveButton = sButton
            .clone()
            .attr("data-action", "remove")
            .text("Remove");
        actionButtonBufferList.push(RemoveButton);
        */
        if (status != "online") {
            kickButton.addClass("disabled");
        }
        if (player.playerCategory == "Blacklisted") {
            banButton.addClass("disabled");
        }
        if (player.playerCategory == "Whitelisted") {
            WLButton.addClass("disabled");
        }
        if (player.playerCategory == "Admin") {
            AdminButton.addClass("disabled");
        }
        if (player.playerName == "") {
            kickButton.addClass("disabled");
            banButton.addClass("disabled");
            WLButton.addClass("disabled");
            AdminButton.addClass("disabled");
            ResetButton.addClass("disabled");
        }
    }
    actionButtonBufferList.forEach((element) => {
        DDMenu.append(element);
    });
    return dropDownDiv.prop("outerHTML");
};
$(document).on("input", "#WLPlayerInp", function (e) {
    console.log($(e.target).val());
    $("#WLPlayerBtn").attr({ "data-name": $(e.target).val() });
});

$(document).on("click", ".pBtn", function (e) {
    e.preventDefault();
    pGuid = $(e.target).attr("data-guid");
    pName = $(e.target).attr("data-name");
    pAction = $(e.target).attr("data-action");

    $.ajax({
        type: "POST",
        url: apiURL + "/player",
        dataType: "json",
        data: JSON.stringify({ guid: pGuid, action: pAction, name: pName }),
        success: function (result) {},
        error: function (result) {
            console.log(result);
            alert("Error");
        },
    });
});

const saveLog = function (filename, data) {
    var blob = new Blob([data], { type: "text/csv" });
    if (window.navigator.msSaveOrOpenBlob) {
        window.navigator.msSaveBlob(blob, filename);
    } else {
        var elem = window.document.createElement("a");
        elem.href = window.URL.createObjectURL(blob);
        elem.download = filename;
        document.body.appendChild(elem);
        elem.click();
        document.body.removeChild(elem);
    }
};

$(".fa-download").click(function (e) {
    e.stopPropagation();

    fileBuffer = "";
    logList.forEach((entry) => {
        fileBuffer += entry;
        fileBuffer += "\n";
    });

    saveLog("server.log", fileBuffer);
});

$("#saveGameBtn").click(function (e) {
    e.preventDefault();
    statusMsg("saving");
    $.ajax({
        type: "POST",
        url: apiURL + "/savegame",
        dataType: "json",
        success: function (result) {},
        error: function (result) {
            console.log(result);
            alert("Error");
        },
    });
});

$("#rebootServerBtn").click(function (e) {
    e.preventDefault();
    statusMsg("reboot");
    $.ajax({
        type: "POST",
        url: apiURL + "/reboot",
        dataType: "json",
        success: function (result) {},
        error: function (result) {
            console.log(result);
            alert("Error");
        },
    });
});

$("#stopLauncherBtn").click(function (e) {
    e.preventDefault();
    statusMsg("shutdown");
    let reallyShutdown = confirm(
        "Are you sure you want to shut down the launcher? It will have to be manually restarted."
    );
    if (reallyShutdown == true) {
        setTimeout(() => {
            statusMsg("off");
        }, 2000);
        $.ajax({
            type: "POST",
            url: apiURL + "/shutdown",
            dataType: "json",
            success: function (result) {},
            error: function (result) {
                console.log(result);
            },
        });
    }
});

const linkify = (text) => {
    //const exp = /(\b(((https?|ftp|file):\/\/)|[-A-Z0-9+&@#\/%=~_|]*\.)[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi;
    const exp = /(\b(((https?|ftp|file):\/\/)|[-A-Z+&@#\/%=~_|]+\.)[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi;
    return text.replace(
        exp,
        `<a href="$1" target="_blank" style="color: #baf;">$1</a>`
    );
};

var clipboard = new ClipboardJS(".ctc");

clipboard.on("success", function (e) {
    e.clearSelection();
});

tippy(".ctc", {
    content: "Copied!",
    trigger: "click",
    onShow(instance) {
        setTimeout(() => {
            instance.hide();
        }, 1500);
    },
    placement: "right",
});

tippy(".ctc", {
    content: "Click to Copy",
    trigger: "mouseenter focus",
    placement: "right",
    onTrigger(instance, event) {
        if (tippy.currentInput.isTouch) {
            instance.disable();
        } else {
            instance.enable();
        }
    },
});

tippy("#githubLink", {
    content: "Update Available",
    placement: "right-end",
    trigger: "manual",
    hideOnClick: false,
    theme: "update",
    interactive: true,
});
