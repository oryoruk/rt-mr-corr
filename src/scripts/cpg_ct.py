import sys
sys.path.append("/project/voight_subrate/avarun/Research/mutation_rate")
from modules import *
from function_wrapper import *
import pandas as pd
import itertools
import pickle

def get_seq_context_variant(chr_name,position,before,after):
    #Chr_name: chromosome name
    #position: position of variant
    #before after: nucleotides before or after the variant
    files = file_handles("/project/voight_subrate/avarun/Research/fasta_file_hg19")
    chr_name = str(chr_name)
    position = int(position)
    before = int(before)
    after = int(after)
    str_around = files.fetch_str_var(chr_name,position,before,after) #string around the variant including it
    #print "sequence context "+str(before)+" basepairs before and "+str(after)+" after the variant including the middle position"+''.join(str_around)
    #return ''.join(str_around)
    return ''.join(str_around)

def get_seq_context_interval(chr_name,start_p,end_p,before_after):
    #Chr_name: chromosome name
    #start_p: start position of interval
    #end_p: end postion of interval
    #before_after: nucleotides before or after the start/end (needed for padding)
    files = file_handles("/project/voight_subrate/avarun/Research/fasta_file_hg19")
    chr_name = str(chr_name)
    start_p = int(start_p)
    end_p = int(end_p)
    before_after = int(before_after)
    acceptable_chr_name = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X"]
    if chr_name in acceptable_chr_name:
        seq = ''.join(files.get_string(chr_name, start_p, end_p, before_after, before_after))
        return seq
    else:
        print "Chromosome entered is not valid"

#def get_seq_context_variant(chr_name,position,before,after):
#    return random.choice(cpg_contexts.keys())

def reverse_complement(seq):
    complement_code = dict( zip( "ATCGNatcgn" , "TAGCNtagcn" ) )
    #return "".join( complement_code[nuc] for nuc in reversed(seq) )
    return "".join( complement_code[nuc] for nuc in seq[::-1] )

def check_if_c_to_t(snps,chrom,chrom_start,reverse_strand = False):
    snp_at_site = snps[(snps.chrom==chrom)&(snps.chrom_start==chrom_start)]
    if snp_at_site.empty:
        return False
    #if there is a snp:
    else:
        #is it g to a (in)
        if reverse_strand:
            if (snp_at_site.iloc[0].ref == 'G') and (snp_at_site.iloc[0].alt == 'A'):
                return True
            else:
                return False
        else:
            if (snp_at_site.iloc[0].ref == 'C') and (snp_at_site.iloc[0].alt == 'T'):
                return True
            else:
                return False


job_index = int(sys.argv[1])

context_size = 7
before = (context_size-1)/2
after = (context_size-1)/2

#cpg_file = './../../data/formatted_regions_sites/reg_whole__acc_nc_auto_cpg.bed'
cpg_file = './../../data/formatted_regions_sites/reg_whole__nc2_cpg.bed'
snp_file = './../../data/mutation_datasets/snp/all_var_EUR_chr_loc_sorted'
output_file = './../../output/initial_analysis/cpg_ct/' + str(job_index)
#output_file = './../../output/initial_analysis/cpg_ct_rt/' + save_file_name


cpg_columns = ['chrom','chrom_start','chrom_end']

#initialization of dictionary to hold info on all contexts:
cpg_contexts = {}
nucs = list('GATC')
for temp in itertools.product(nucs,repeat = 5):
    context = ''.join(temp[:3]) + 'CG' + ''.join(temp[3:])
    cpg_contexts[context] = [0,0]

cpg_sites = pd.read_csv(cpg_file, delimiter = '\t', header = None, names = cpg_columns, dtype ={'chrom':object})
#subset of cpg sites that this job needs to consider:
cpg_sites = cpg_sites[job_index*10**4:(job_index+1)*10**4]

snps = pd.read_csv(snp_file, delimiter = '\t', header = None, names = ['chrom','chrom_start','ref','alt','alt2','id','freq'], dtype ={'chrom':object})
#snps.sort_values(['chrom','chrom_start'],ascending=[1,1], inplace=True)
#snps.reset_index(drop=True,inplace=True)
#subset of snps that this job needs to consider:
slice_start_chrom = cpg_sites.head(1).chrom.iloc[0]
slice_end_chrom = cpg_sites.tail(1).chrom.iloc[0]
slice_start_chrom_start = cpg_sites.head(1).chrom_start.iloc[0]
slice_end_chrom_end = cpg_sites.tail(1).chrom_end.iloc[0]
slice_start_index = snps[(snps.chrom == slice_start_chrom)&(snps.chrom_start >= slice_start_chrom_start)].head(1).index[0]
slice_end_index = snps[(snps.chrom == slice_end_chrom)&(snps.chrom_start < slice_end_chrom_end)].tail(1).index[0] + 1
snps = snps[slice_start_index : slice_end_index ]

exception_counter = 0
for i, cpg_site in cpg_sites.iterrows():

    #here is the first part: 1ST NUCLEOTIDE in CpG:
    try:
        cpg_context = get_seq_context_variant(cpg_site.chrom, cpg_site.chrom_start, before, after)
    except:
        cpg_context = ''
        exception_counter += 1

    if cpg_context in cpg_contexts:
        cpg_contexts[cpg_context][0]+=1
        #check if it is c to t sub via 1KG EUR (or other SNP) File
        c_to_t_sub = check_if_c_to_t(snps,cpg_site.chrom,cpg_site.chrom_start,reverse_strand = False)
        if c_to_t_sub:
            cpg_contexts[cpg_context][1] += 1

    #here is the second part: 2ND NUCLEOTIDE in CpG:
    try:
        cpg_context = get_seq_context_variant(cpg_site.chrom, cpg_site.chrom_start + 1, before, after)
    except:
        cpg_context = ''
        exception_counter += 1

    #DELETE THIS NEXT LINE: it's only for the mock function
    #cpg_context = reverse_complement(cpg_context)
    if reverse_complement(cpg_context) in cpg_contexts:
        cpg_contexts[reverse_complement(cpg_context)][0]+=1
        c_to_t_sub = check_if_c_to_t(snps, cpg_site.chrom,cpg_site.chrom_start + 1,reverse_strand = True)
        if c_to_t_sub:
            cpg_contexts[reverse_complement(cpg_context)][1] += 1

print exception_counter
#save dictionary:
fileObject = open(output_file, 'wb')
pickle.dump(cpg_contexts, fileObject)
fileObject.close()