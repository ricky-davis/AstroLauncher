console.log("Hi there! Feel to explore the code!");

$ = document.querySelector.bind(document);
let playersTableOriginal = $("#players").innerHTML
const init = async () => {
  try {
    let res = await fetch("/api");
    const data = await res.json();

    //console.log(data);

    s = data.settings;

    $("#titleIP").innerHTML = `${s.PublicIP}:${s.Port}`;

    $("#serverName").innerHTML = s.ServerName;
    $("#owner").innerHTML = s.OwnerName;
    $("#maxFramerate").innerHTML = parseFloat(s.MaxServerFramerate);

    $("#maxPlayers").innerHTML = s.MaximumPlayerCount;
    $("#onlinePlayers").innerHTML = data.players.playerInfo.filter(
      (p) => p.inGame
    ).length;

    if (data.players) {
      $("#players").innerHTML = playersTableOriginal
      data.players.playerInfo.forEach((p) => {
        let row = document.createElement("tr");
        row.innerHTML = `<td>${p.playerName}</td>
          <td>${p.playerCategory}</td>
          <td>${p.inGame}</td>`;

        $("#players").appendChild(row);
      });
    } else {
      $("#players").innerHTML = "Error getting player data";
    }
  } catch (e) {
    $("#msg").innerHTML = "ERROR! Try again in 10s";
    $("#msg").style.display = "block";
  }
};
setInterval(init, 2000);
init()
