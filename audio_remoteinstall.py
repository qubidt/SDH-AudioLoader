import asyncio, json, tempfile, os
from audio_utils import Result, Log
from audio_utils import AUDIO_LOADER_VERSION
import aiohttp

async def run(command : str) -> str:
    proc = await asyncio.create_subprocess_shell(command,        
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()

    if (proc.returncode != 0):
        raise Exception(f"Process exited with error code {proc.returncode}")

    return stdout.decode()

async def install(id : str, base_url : str) -> Result:
    if not base_url.endswith("/"):
        base_url = base_url + "/"

    url = f"{base_url}themes/{id}"

    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(f"Invalid status code {resp.status}")

                data = await resp.json()
    except Exception as e:
        return Result(False, str(e))
    
    if (data["manifestVersion"] > AUDIO_LOADER_VERSION):
        raise Exception("Manifest version of entry is unsupported by this version of Audio Loader")

    download_url = f"{base_url}blobs/{data['download']['id']}" 
    tempDir = tempfile.TemporaryDirectory()

    Log(f"Downloading {download_url} to {tempDir.name}...")
    themeZipPath = os.path.join(tempDir.name, 'theme.zip')
    try:
        await run(f"curl \"{download_url}\" -L -o \"{themeZipPath}\"")
    except Exception as e:
        return Result(False, str(e))

    Log(f"Unzipping {themeZipPath}")
    try:
        await run(f"unzip -o \"{themeZipPath}\" -d \"/home/deck/homebrew/sounds\"")
    except Exception as e:
        return Result(False, str(e))

    tempDir.cleanup()

    # for x in data["dependencies"]:
    #     if x["name"] in local_themes:
    #         continue
            
    #     await install(x["id"], base_url, local_themes)
    
    return Result(True)