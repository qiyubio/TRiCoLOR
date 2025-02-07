#!/usr/bin/python3 env

#python 3 standard library

from datetime import date
import os
from operator import itemgetter

#additional modules

import pysam
from bisect import bisect_left,bisect_right
import editdistance


def VCF_headerwriter(c):

	'''
	Write VCF header and return BAM header
	'''

	bamfile=pysam.AlignmentFile(c.BAM[0],'rb')
	header=bamfile.header
	chromosomes_info=list(header.items())[1][1]
	bamfile.close()


	vcf_format='##fileformat=VCFv4.2'
	SVEND='##INFO=<ID=TREND,Number=1,Type=Integer,Description="Repetition end">'
	SVLEN='##INFO=<ID=TRLEN,Number=1,Type=Integer,Description="Length of the ALT allele (the shortest if multiple ALT alleles)">'
	RAED = '##INFO=<ID=RAED,Number=1,Type=Integer,Description="Edit distance between REF and most similar ALT allele">'
	AED = '##INFO=<ID=AED,Number=1,Type=Integer,Description="Edit distance between ALT alleles">'
	MAPQ1 = '##INFO=<ID=MAPQ1,Number=1,Type=Integer,Description="Mapping quality of the consensus sequence from 1st haplotype">'
	MAPQ2 = '##INFO=<ID=MAPQ2,Number=1,Type=Integer,Description="Mapping quality of the consensus sequence from 2nd haplotype">'	
	H1M='##INFO=<ID=H1M,Number=.,Type=String,Description="Repeated Motif on 1st Haplotype">'
	H1N='##INFO=<ID=H1N,Number=.,Type=Integer,Description="Repetitions Number on 1st Haplotype">'
	H2M='##INFO=<ID=H2M,Number=.,Type=String,Description="Repeated Motif on 2nd Haplotype">'
	H2N='##INFO=<ID=H2N,Number=.,Type=Integer,Description="Repetitions Number on 2nd Haplotype">'
	FORMAT1='##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">'
	FORMAT2 = '##FORMAT=<ID=DP1,Number=1,Type=Integer,Description="Coverage depth on 1st haplotype">'
	FORMAT3 = '##FORMAT=<ID=DP2,Number=1,Type=Integer,Description="Coverage depth on 2nd haplotype">'
	classic_header='#CHROM' + '\t' + 'POS' '\t' + 'ID' + '\t' + 'REF' + '\t' + 'ALT' + '\t' + 'QUAL' + '\t' + 'FILTER' + '\t' + 'INFO' + '\t' + 'FORMAT' + '\t' + c.samplename.upper()

	with open(os.path.abspath(c.OUT + '/TRiCoLOR.srt.vcf'), 'w') as vcfout:

		vcfout.write(vcf_format + '\n' + '##filedate=' + ''.join(str(date.today()).split('-')) +  '\n' + '##source=TRiCoLOR' + '\n')

		for x in chromosomes_info:

			vcfout.write('##contig=<ID='+str(x['SN'])+',length='+str(x['LN'])+'>'+'\n')

		vcfout.write(SVEND + '\n' + SVLEN + '\n' + RAED + '\n' + AED + '\n' + MAPQ1 + '\n' + MAPQ2 + '\n' + H1M + '\n' + H1N + '\n' + H2M + '\n' + H2N + '\n')
		vcfout.write(FORMAT1 + '\n' + FORMAT2 + '\n' + FORMAT3 + '\n')
		vcfout.write('##SAMPLE=<ID=' + c.samplename.upper() +'>' + '\n' + classic_header + '\n')

	return header


def VCF_variantwriter(CHROM, POS, REF, ALT, INFO, FORMAT):

	'''
	Combine informations into a variant entry
	'''

	ID='.'
	FILTER='.'
	QUAL='.'
	GEN='GT:DP1:DP2'
	
	INFO_SVEND=str(INFO['SVEND']+1) #convert to 1-based coordinate, also for POS
	INFO_SVLEN=str(INFO['SVLEN'])
	INFO_RAED = str(INFO['RAED'])
	INFO_AED = str(INFO['AED'])
	INFO_MAPQ1=str(INFO['MAPQ1'])
	INFO_MAPQ2=str(INFO['MAPQ2'])

	INFO_H1M=INFO['H1M']

	if type(INFO_H1M) == list:

		INFO_H1M = ','.join(str(x) for x in INFO_H1M) 

	INFO_H1N=INFO['H1N']

	if type(INFO_H1N) == list:

		INFO_H1N = ','.join(str(x) for x in INFO_H1N) 

	INFO_H2M=INFO['H2M']

	if type(INFO_H2M) == list:

		INFO_H2M = ','.join(str(x) for x in INFO_H2M) 

	INFO_H2N=INFO['H2N']

	if type(INFO_H2N) == list:

		INFO_H2N = ','.join(str(x) for x in INFO_H2N) 

	FORMAT_GT=FORMAT['GT']
	FORMAT_DP1 = str(FORMAT['DP1'])
	FORMAT_DP2 = str(FORMAT['DP2'])

	variant=CHROM + '\t' + str(POS+1) + '\t' + ID + '\t' + REF + '\t' + ALT + '\t' + QUAL + '\t' + FILTER + '\t' + 'TREND='+INFO_SVEND + ';'+ 'TRLEN='+ INFO_SVLEN + ';' + 'RAED='+ INFO_RAED + ';' + 'AED=' + INFO_AED + ';' + 'MAPQ1=' + INFO_MAPQ1 + ';' + 'MAPQ2=' + INFO_MAPQ2 + ';' + 'H1M='+INFO_H1M + ';' + 'H1N='+INFO_H1N + ';' + 'H2M='+INFO_H2M + ';' + 'H2N='+INFO_H2N + '\t' + GEN + '\t' + FORMAT_GT + ':' + FORMAT_DP1 + ':' + FORMAT_DP2 + '\n'

	return variant


def recursive_merge(sorted_int, list_, i):

	'''
	Recursively merge if previous merge created another interval overlapping others
	'''

	new_=(min(list_, key=itemgetter(1)), max(list_,key=itemgetter(2)))
	new_range=(new_[0][1], new_[-1][2])

	if i < len(sorted_int) -1:

		if sorted_int[i+1][1] <= new_range[1]:

			list_.append(sorted_int[i+1])
			recursive_merge(sorted_int, list_, i+1)


def Merger(sorted_int,refreps,h1reps,h2reps):

	'''
	Merge intervals
	'''

	sorted_ranges=[]

	ref_dict_number=dict()
	ref_dict_motif=dict()

	hap1_dict_number=dict()
	hap1_dict_motif=dict()

	hap2_dict_number=dict()
	hap2_dict_motif=dict()

	i=0

	while i < len(sorted_int):

		reps=sorted_int[i]
		to_int=sorted_int[i+1:]
		list_=[]
		l=0

		for elem in to_int:

			if elem[1] <= reps[2]:

				l+=1

				list_.append(elem)

		if len(list_) != 0:

			list_.append(reps)
			recursive_merge(sorted_int, list_, i+len(list_)-1) #? ANY BETTER IDEA THAN RECURSION? NOT PRIORITY.
			new_=(min(list_, key=itemgetter(1)), max(list_,key=itemgetter(2)))
			new_range=(new_[0][1], new_[-1][2])

			for el_ in list_:

				if el_ in refreps:

					if new_range not in ref_dict_motif:

						ref_dict_motif[new_range]= [el_[0]]
						ref_dict_number[new_range]= [el_[3]]

					else:

						ref_dict_motif[new_range].append(el_[0])
						ref_dict_number[new_range].append(el_[3])

				if el_ in h1reps:

					if new_range not in hap1_dict_motif:

						hap1_dict_motif[new_range]= [el_[0]]
						hap1_dict_number[new_range]= [el_[3]]

					else:

						hap1_dict_motif[new_range].append(el_[0])
						hap1_dict_number[new_range].append(el_[3])

				if el_ in h2reps:

					if new_range not in hap2_dict_motif:

						hap2_dict_motif[new_range]= [el_[0]]
						hap2_dict_number[new_range]= [el_[3]]

					else:

						hap2_dict_motif[new_range].append(el_[0])
						hap2_dict_number[new_range].append(el_[3])

			i+=len(list_)
			sorted_ranges.append(new_range)

		else:

			new_range=((reps[1], reps[2]))

			if reps in refreps:

				if new_range not in ref_dict_motif:

					ref_dict_motif[new_range]= [reps[0]]
					ref_dict_number[new_range]= [reps[3]]

				else:

					ref_dict_motif[new_range].append(reps[0])
					ref_dict_number[new_range].append(reps[3])

			if reps in h1reps:

				if new_range not in hap1_dict_motif:

					hap1_dict_motif[new_range]= [reps[0]]
					hap1_dict_number[new_range]= [reps[3]]

				else:

					hap1_dict_motif[new_range].append(reps[0])
					hap1_dict_number[new_range].append(reps[3])


			if reps in h2reps:

				if new_range not in hap2_dict_motif:

					hap2_dict_motif[new_range]= [reps[0]]
					hap2_dict_number[new_range]= [reps[3]]

				else:

					hap2_dict_motif[new_range].append(reps[0])
					hap2_dict_number[new_range].append(reps[3])

			if not new_range in sorted_ranges:

				sorted_ranges.append(new_range)

			i += 1

	return sorted_ranges,ref_dict_number,ref_dict_motif,hap1_dict_number,hap1_dict_motif,hap2_dict_number,hap2_dict_motif


def modifier(seq,coords,POS,SVEND):

	'''
	Modify coordinates. This is a trick-function that avoids errors if a coordinate is outside range
	'''

	NewSeq=''
	coords_purified=[]

	for i in range(len(coords)-1):

		if coords[i+1]-coords[i] > 1:

			coords_purified.append(coords[i])
			coords_purified.extend(list(range(coords[i]+1,coords[i+1])))
			NewSeq+=seq[i]
			NewSeq+="-"*(coords[i+1]-coords[i]-1)

		else:

			coords_purified.append(coords[i])
			NewSeq+=seq[i]

	coords_purified.append(coords[-1])
	NewSeq+=seq[-1]

	if not POS >= coords_purified[0]:

		number=POS
		how_many=coords_purified[0]-POS
		coords_purified = [number]*how_many + coords_purified
		NewSeq= '-'* how_many + NewSeq

	if not SVEND <= coords_purified[-1]:

		number=SVEND
		how_many=SVEND - coords_purified[-1]
		coords_purified = coords_purified + [number]*how_many 
		NewSeq= NewSeq + '-'* how_many

	return NewSeq,coords_purified


def GetIndex(start,end,coordinates):

	'''
	Retrieve index corresponding to coordinate
	'''

	si=bisect_left(coordinates, start)
	ei=bisect_right(coordinates, end)

	return si,ei


def VCF_writer(chromosome,repsref,reference_sequence,repsh1,seqh1,coordsh1,covh1,qual1,repsh2,seqh2,coordsh2,covh2,qual2):

	'''
	Process possible combinations.
	'''

	intersection=set(repsref+repsh1+repsh2)
	variants=[]

	if len(intersection) != 0:

		sorted_intersection=sorted(intersection, key=itemgetter(1,2))
		sorted_ranges,ref_dict_number,ref_dict_motif,hap1_dict_number,hap1_dict_motif,hap2_dict_number,hap2_dict_motif=Merger(sorted_intersection,repsref,repsh1,repsh2)

		for reps in sorted_ranges:

			CHROM=chromosome
			POS=reps[0]
			SVEND=reps[1]
			REF=reference_sequence[POS:SVEND+1] #extract correct sequence from REF

			if reps in hap1_dict_number.keys():

				seqh1_,coordsh1_=modifier(seqh1,coordsh1,POS,SVEND)

				IS1,IE1=GetIndex(POS,SVEND,coordsh1_)
				ALT1=seqh1_[IS1:IE1].replace('-','')
				H1N=hap1_dict_number[reps]
				H1M=hap1_dict_motif[reps]
				DP1=covh1

			else:

				if seqh1 == []:

					ALT1='.'
					H1N='.'
					H1M='.'
					
					if covh1 == []:

						DP1='.'

					else:

						DP1=covh1

				else:

					seqh1_,coordsh1_=modifier(seqh1,coordsh1,POS,SVEND)
					IS1,IE1=GetIndex(POS,SVEND,coordsh1_)
					ALT1=seqh1_[IS1:IE1].replace('-','')
					H1N='.'
					H1M='.'
					DP1=covh1

			if reps in hap2_dict_number.keys():

				seqh2_,coordsh2_=modifier(seqh2,coordsh2,POS,SVEND)
				IS2,IE2=GetIndex(POS,SVEND,coordsh2_)
				ALT2=seqh2_[IS2:IE2].replace('-','')
				H2N=hap2_dict_number[reps]
				H2M=hap2_dict_motif[reps]
				DP2=covh2

			else:

				if seqh2 == []:

					ALT2='.'
					H2N='.'
					H2M='.'
					
					if covh2 == []:

						DP2='.'

					else:

						DP2=covh2

				else:

					seqh2_,coordsh2_=modifier(seqh2,coordsh2,POS,SVEND)
					IS2,IE2=GetIndex(POS,SVEND,coordsh2_)
					ALT2=seqh2_[IS2:IE2].replace('-','')
					H2N='.'
					H2M='.'
					DP2=covh2

			if seqh1 == [] and seqh2 == []:

				GEN1='.'
				GEN2='.'
				ALT = '.'
				SVLEN='.'
				MAPQ1='.'
				MAPQ2='.'

			elif seqh1 != [] and seqh2 == []:

				GEN2='.'

				if ALT1 == REF:

					GEN1 = '0'
					ALT = '.'

				else:

					GEN1 = '1'
					ALT = ALT1

				SVLEN=len(ALT1)
				MAPQ1=qual1
				MAPQ2='.'

			elif seqh1 == [] and seqh2 != []:

				GEN1='.'

				if ALT2 == REF:

					GEN2 = '0'
					ALT = '.'

				else:

					GEN2 = '1'
					ALT = ALT2

				SVLEN=len(ALT2)
				MAPQ1='.'
				MAPQ2=qual2

			else:

				if ALT1 == REF and ALT2 == REF:

					#GEN1 = '0'
					#GEN2 = '0'
					#ALT= '.'
					continue

				elif ALT1 == REF and ALT2 != REF:

					GEN1= '0'
					GEN2 = '1'
					ALT = ALT2
					SVLEN=len(ALT2)

				elif ALT1 != REF and ALT2 == REF:

					GEN1= '1'
					GEN2 = '0'
					ALT = ALT1
					SVLEN=len(ALT1)

				else:

					if ALT1 == ALT2:

						GEN1 = '1'
						GEN2 = '1'
						ALT = ALT1

					else:

						GEN1 = '1'
						GEN2 = '2'
						ALT = ALT1 + ',' + ALT2

					SVLEN=min(len(ALT1),len(ALT2))
					
				MAPQ1=qual1
				MAPQ2=qual2

			GEN = GEN1 + '|' + GEN2

			INFO=dict()
			INFO['SVEND'] = SVEND

			if ALT1 == '.' and ALT2 == '.':

				RAED = '.'
				AED = '.'

			elif ALT1 != '.' and ALT2 == '.':

				RAED = editdistance.eval(REF, ALT1)
				AED= '.'

			elif ALT1 == '.' and ALT2 != '.':

				RAED = editdistance.eval(REF, ALT2)
				AED='.'

			else:

				RAED1=editdistance.eval(REF, ALT1)
				RAED2=editdistance.eval(REF, ALT2)

				if RAED1 < RAED2:

					RAED = RAED1

				else:

					RAED = RAED2

				AED = editdistance.eval(ALT1,ALT2)

			INFO['SVLEN'] = SVLEN 
			INFO['RAED'] = RAED
			INFO['AED'] = AED
			INFO['MAPQ1'] = MAPQ1
			INFO['MAPQ2'] = MAPQ2
			INFO['H1M'] = H1M
			INFO['H1N'] = H1N
			INFO['H2M'] = H2M 
			INFO['H2N'] = H2N

			FORMAT = dict()

			FORMAT['GT'] = GEN
			FORMAT['DP1'] = DP1
			FORMAT['DP2'] = DP2

			variant=VCF_variantwriter(CHROM, POS, REF, ALT, INFO, FORMAT)
			variants.append((variant,POS))

	return variants