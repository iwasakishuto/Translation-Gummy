// Initialization.
document.getElementById("loading").style.display ="none";
function long_load(){
  setTimeout(
    function () {
      const loading  = document.getElementById("loading");
      const contents = document.getElementById("contents");
      loading.style.display="block";
      contents.style.display="none";
    },
    "1000"
  );
};