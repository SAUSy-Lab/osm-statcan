import os
import subprocess

def main():
    program = "tools/osmconvert64"

    inputDir = "data/osm"
    osmFiles = [os.path.join(inputDir, f) for f in os.listdir(inputDir) if os.path.isfile(os.path.join(inputDir, f))]
    outputDir = "data/osm/batches"

    for i in range(len(osmFiles) // 100):
        args = [program] + osmFiles[i * 100:i * 100 + 100] + ["-o={0}/batch{1}.osm".format(outputDir, i)]
        subprocess.run(args)
    
    args = [program] + osmFiles[(len(osmFiles) // 100) * 100:] + ["-o={0}/batch{1}.osm".format(outputDir, len(osmFiles) // 100)]
    subprocess.run(args)

    inputDir = "data/osm/batches"
    osmFiles = [os.path.join(inputDir, f) for f in os.listdir(inputDir) if os.path.isfile(os.path.join(inputDir, f))]
    outputDir = "data/osm/merged"
    
    args = [program] + osmFiles + ["-o={}/merged.osm".format(outputDir)]
    subprocess.run(args)

if __name__ == "__main__":
    main()
