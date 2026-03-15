export function BrazilFlag() {
  return (
    <svg width="24" height="24" viewBox="0 0 512 512">
      <path fill="#6DA544" d="M512 256c0 141.384-114.616 256-256 256S0 397.384 0 256 114.616 0 256 0s256 114.616 256 256z"/>
      <path fill="#FFDA44" d="M256 100.174L467.478 256 256 411.826 44.522 256z"/>
      <circle fill="#F0F0F0" cx="256" cy="256" r="89.043"/>
      <g fill="#0052B4">
        <path d="M211.478 250.435c-15.484 0-30.427 2.355-44.493 6.725.623 48.64 40.227 87.884 89.015 87.884 30.168 0 56.812-15.017 72.919-37.968-27.557-34.497-69.958-56.641-117.441-56.641z"/>
        <path d="M343.393 273.06a89.45 89.45 0 0 0 1.651-17.06c0-49.178-39.866-89.043-89.043-89.043-41.543 0-76.394 28.937-85.516 67.097 15.897-5.126 32.847-7.911 50.537-7.911 49.559 0 93.776 22.369 122.371 46.917z"/>
      </g>
    </svg>
  )
}

export function UKFlag() {
  return (
    <svg width="24" height="24" viewBox="0 0 512 512">
      <defs>
        <clipPath id="circle">
          <circle cx="256" cy="256" r="256"/>
        </clipPath>
      </defs>
      <g clipPath="url(#circle)">
        <path fill="#012169" d="M0 0h512v512H0z"/>
        <path fill="#FFF" d="M512 0v64L322 256l190 187v69h-67L254 324 68 512H0v-68l186-187L0 74V0h62l192 188L440 0z"/>
        <path fill="#C8102E" d="M184 324l11 34L42 512H0v-3l184-185zm124-12l54 8 150 147v45L308 312zM512 0L320 196l-4-44L466 0h46zM0 1l193 189-59-8L0 49V1z"/>
        <path fill="#FFF" d="M176 0v512h160V0H176zM0 176v160h512V176H0z"/>
        <path fill="#C8102E" d="M0 208v96h512v-96H0zM208 0v512h96V0h-96z"/>
      </g>
    </svg>
  )
}

export function SpainFlag() {
  return (
    <svg width="24" height="24" viewBox="0 0 512 512">
      <defs>
        <clipPath id="circle">
          <circle cx="256" cy="256" r="256"/>
        </clipPath>
      </defs>
      <g clipPath="url(#circle)">
        <path fill="#FFC700" d="M0 128h512v256H0z"/>
        <path fill="#C60B1E" d="M0 0h512v128H0zM0 384h512v128H0z"/>
        <g transform="translate(163,192)">
          <path fill="#C60B1E" d="M57 0h70v183H57z"/>
          <path fill="#FFC700" d="M0 183v-48c0-71 57-71 57-71h70s57 0 57 71v48H0z"/>
          <path fill="#C60B1E" d="M57 107v76h70v-76c0-24-18-41-35-41-17 0-35 17-35 41z"/>
          <path fill="#FF9811" d="M74 41h35L92 0z"/>
          <circle fill="#FF9811" cx="92" cy="41" r="11"/>
        </g>
      </g>
    </svg>
  )
} 