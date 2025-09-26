# Symbolic links

## Why the project makes use of symlinks
In a distributed job scheduling system like Antares Winjobs, efficient file sharing between the driver and worker nodes is crucial.  
To facilitate this, antares winjobs utilizes **directory symlinks** on Windows systems.  
This approach allows driver and workers to exchange files without requiring dedicated file share protocols. 
By creating symlinks in a consist manner across machines, they can exchange file paths seamlessly.

Example:
- Driver has a local disk C: symlinked to C:\links\drives\c.
- Driver shares this link over the network as \\driver\c.
- Driver creates a symlink to his own share in C:\links\driver_c
- Worker also creates a symlink to that share in C:\links\driver_c
- Both driver and worker can now access the same files via C:\links\driver_c, without needing direct network connections.

## How are Symlinks different from Junctions?
**Junctions** and **symlinks** are both special filesystem objects that point to other directories or files.  
However, **Junctions** can only reference local folders, not network shares which makes them unsuitable for our use case.
On the contrary, **Symlinks** can point to both local and remote locations, but they require admin privileges to create.

## How Are They Created?
The repo provide two setup scripts in the `scripts` folder:

- `setup_symlinks_local.py`:  
  Creates symlinks/junctions for each local fixed disk drive and shares them over the network.  
  **Requires:** Run from an administrator command prompt.

- `setup_symlinks_remote.py`:  
  Creates symlinks to network shares on remote machines, after the local setup is complete.  
  **Requires:** Run from an administrator command prompt.


## Is It Safe to Remove Junctions/Symlinks?
It is safe to delete junctions and symlinks using Windows Explorer or the command line.  
**Deleting a link only removes the link itself, not the target files or directories.**  
The underlying data remains untouched.
