import React from 'react';
import html2canvas from 'html2canvas';

function ShareResult({ isforOne }) {
  function download(dataurl, filename) {
    const link = document.createElement('a');
    link.href = dataurl;
    link.download = filename;
    link.click();
  }

  async function share() {
    await html2canvas(document.getElementById('resultonepage')).then(async canvas => {
      await canvas.toBlob(function (blob) {
        download(URL.createObjectURL(blob), 'result.png');
      }, 'image/png');
    });
  }

  return (
    <button
      onClick={share}
      className={`font-cookierun deskTop:text-2xl mobile:text-lg px-[1.5rem] py-[0.3rem] rounded-full 
                whitespace-nowrap ${isforOne ? 'bg-primary-3 text-primary-1' : 'bg-black text-primary'}`}
    >
      결과저장
    </button>
  );
}

export default ShareResult;
