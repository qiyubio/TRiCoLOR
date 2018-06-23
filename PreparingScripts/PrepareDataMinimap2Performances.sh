#!/bin/bash

### Minimap2 performances ##

# Number of reads per file

find . -name "*gz" > FileNames.txt
find . -name "*.gz" | while read -r file; do zcat -f "$file" | wc -l ; done > FileLengths.txt #has to be divided by 4 as each sequence is described by 4 lines in .fastq file



# Time of Analysis with minimap2

# Without trimming on length/quality

# samtools 1.7
# htsbox r340


MyFiles="HG00733_lib01_20171205_FAH36618_DD_guppy_0.5.1.fq.gz HG00733_lib01_20171205_FAH36664_DD_guppy_0.5.1.fq.gz HG00733_lib01_20171205_FAH36718_DD_guppy_0.5.1.fq.gz HG00733_lib02_20171207_FAH36590_DD_guppy_0.5.1.fq.gz HG00733_lib02_20171207_FAH36591_DD_guppy_0.5.1.fq.gz HG00733_lib02_20171207_FAH36626_DD_guppy_0.5.1.fq.gz HG00733_lib02_20171207_FAH36653_DD_guppy_0.5.1.fq.gz HG00733_lib03_20171207_FAH36732_DD_guppy_0.5.1.fq.gz HG00733_lib04_20171213_FAH36433_DD_guppy_0.5.1.fq.gz HG00733_lib04_20171213_FAH37423_DD_guppy_0.5.1.fq.gz HG00733_lib04_20171213_FAH37574_DD_guppy_0.5.1.fq.gz HG00733_lib05_20171213_FAH36467_DD_guppy_0.5.1.fq.gz HG00733_lib05_20171213_FAH36476_DD_guppy_0.5.1.fq.gz HG00733_lib05_20171213_FAH36782_DD_guppy_0.5.1.fq.gz HG00733_lib06_20171218_FAH36588_DD_guppy_0.5.1.fq.gz HG00733_lib06_20171218_FAH36624_DD_guppy_0.5.1.fq.gz HG00733_lib06_20171218_FAH36752_DD_guppy_0.5.1.fq.gz"

Hg38mmRef="/home/davideb/nanopore/hg38Reference/hg38.mmi"

FileTime="time.txt"

Time="/usr/bin/time"

for Index in $MyFiles

do 

$Time -p -ao $FileTime minimap2 -ax map-ont -t 10 $Hg38mmRef $Index > $Index".minimap2.sam" &&
htsbox samview -bS $Index.minimap2.sam > $Index".minimap2.bam" &&
rm $Index.minimap2.sam &&
samtools sort -m 5G -@ 10 $Index.minimap2.bam > $Index".minimap2.srt.bam" &&
rm $Index.minimap2.bam &&
samtools index $Index.minimap2.srt.bam &&
mv $Index.minimap2.srt.bam "$(echo "$Index.minimap2.srt.bam" | sed -e 's/.fq.gz//')" &&
mv $Index.minimap2.srt.bam.bai "$(echo "$Index.minimap2.srt.bam.bai" | sed -e 's/.fq.gz//')"

done


cat time.txt | grep "real" | awk '{print $2}' > RealTime.txt

paste -d "\t" FileNames.txt FileLengths.txt RealTime.txt > FileNamesLengthsTime.txt 

rm RealTime.txt 


### distribution of length for each fastq file


MyFiles="HG00733_lib01_20171205_FAH36618_DD_guppy_0.5.1.fq.gz HG00733_lib01_20171205_FAH36664_DD_guppy_0.5.1.fq.gz HG00733_lib01_20171205_FAH36718_DD_guppy_0.5.1.fq.gz HG00733_lib02_20171207_FAH36590_DD_guppy_0.5.1.fq.gz HG00733_lib02_20171207_FAH36591_DD_guppy_0.5.1.fq.gz HG00733_lib02_20171207_FAH36626_DD_guppy_0.5.1.fq.gz HG00733_lib02_20171207_FAH36653_DD_guppy_0.5.1.fq.gz HG00733_lib03_20171207_FAH36732_DD_guppy_0.5.1.fq.gz HG00733_lib04_20171213_FAH36433_DD_guppy_0.5.1.fq.gz HG00733_lib04_20171213_FAH37423_DD_guppy_0.5.1.fq.gz HG00733_lib04_20171213_FAH37574_DD_guppy_0.5.1.fq.gz HG00733_lib05_20171213_FAH36467_DD_guppy_0.5.1.fq.gz HG00733_lib05_20171213_FAH36476_DD_guppy_0.5.1.fq.gz HG00733_lib05_20171213_FAH36782_DD_guppy_0.5.1.fq.gz HG00733_lib06_20171218_FAH36588_DD_guppy_0.5.1.fq.gz HG00733_lib06_20171218_FAH36624_DD_guppy_0.5.1.fq.gz HG00733_lib06_20171218_FAH36752_DD_guppy_0.5.1.fq.gz"


for Index in $MyFiles

do 

zcat $Index | awk '{if(NR%4==2) print length($1)}' > $Index_length.txt && #length of each sequence

zcat $Index | awk '{if(NR%4==2) print length($1)}' | awk '{ sum += $1; n++ } END { if (n > 0) print sum / n; }' > $Index_mean_length.txt #mean length of each .fastq file

done


## end preparing data for minimap2 performances on ONT data ###

## will be plotted in Python ###



#will be plotted in Python


