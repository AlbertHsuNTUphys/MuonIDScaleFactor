import ROOT,math,os
ROOT.gROOT.LoadMacro('./RooCMSShape.cc+')
ROOT.gROOT.LoadMacro('./RooCBExGaussShape.cc+')

from math import sqrt
from ROOT import RooCMSShape,TCanvas, TPad, RooCBExGaussShape
import CMSTDRStyle
CMSTDRStyle.setTDRStyle().cd()
import CMSstyle
from array import array
import re

def muSF(fitType,ismc,filename):

#  filein=ROOT.TFile("./Pt10To20Etam0p0Top0p8.root","READ")
  print("Processing %s"%filename)
  filein=ROOT.TFile(filename,"READ")
  
  dy_pass=ROOT.TH1D()
  dy_fail=ROOT.TH1D()
  Muon_pass=ROOT.TH1D()
  Muon_fail=ROOT.TH1D()
  filein.GetObject("TnP_mass_DYpass",dy_pass)
  filein.GetObject("TnP_mass_DYfail",dy_fail)
  filein.GetObject("TnP_mass_Muonpass",Muon_pass)
  filein.GetObject("TnP_mass_Muonfail",Muon_fail)
  
  DY_pass_error=ROOT.Double(0.)
  DY_fail_error=ROOT.Double(0.)
  Muon_pass_error=ROOT.Double(0.)
  Muon_fail_error=ROOT.Double(0.)
  DY_pass_total=dy_pass.IntegralAndError(1,60,DY_pass_error)
  DY_fail_total=dy_fail.IntegralAndError(1,60,DY_fail_error)
  Muon_pass_total=Muon_pass.IntegralAndError(1,60,Muon_pass_error)
  Muon_fail_total=Muon_fail.IntegralAndError(1,60,Muon_fail_error)
 
  w = ROOT.RooWorkspace() 
  w.factory("x[61,119]")
  x = w.var('x')
#  x = ROOT.RooRealVar("x", "x", 60, 120)
  x.setRange("FitRange", 61, 119)
  
  # make RootDataHist 
  GenPass = ROOT.RooDataHist("GenPass","GenPass",ROOT.RooArgList(x),dy_pass)
  GenFail = ROOT.RooDataHist("GenFail","GenFail",ROOT.RooArgList(x),dy_fail)
  DataPass = ROOT.RooDataHist("DataPass","DataPass",ROOT.RooArgList(x),Muon_pass)
  DataFail = ROOT.RooDataHist("DataFail","DataFail",ROOT.RooArgList(x),Muon_fail)
  
  ZPassShape = ROOT.RooHistPdf("ZPassShape","ZPassShape",ROOT.RooArgSet(x), GenPass)
  ZFailShape = ROOT.RooHistPdf("ZFailShape","ZFailShape",ROOT.RooArgSet(x), GenFail)
  
  # gauss smearing of DY shape
  meanPass = ROOT.RooRealVar("meanP", "mean of Reg", -0.0, -5.0, 5.0)
  sigmaPass = ROOT.RooRealVar("sigmaP", "width of Reg", 0.9,0.5,5.0)
  gauss_Pass = ROOT.RooGaussian("gaussP", "gaussian Reg", x, meanPass, sigmaPass)

  meanFail = ROOT.RooRealVar("meanF", "mean of Reg", -0.0, -5.0, 5.0)
  sigmaFail = ROOT.RooRealVar("sigmaF", "width of Reg", 0.9,0.5,5.0)
  gauss_Fail = ROOT.RooGaussian("gaussF", "gaussian Reg", x, meanFail, sigmaFail)

  # Alternative signal model with RooCBExGaussShape smearing
  tnpAltSigFit = [
   "meanP[-0.0, -5.0, 5.0]", "sigmaP[1, 0.7, 6.0]",
   "alphaP[2.0, 1.2, 3.5]",
   'nP[3, -5, 5]', "sigmaP_2[1.5, 0.5, 6.0]", "sosP[1, 0.5, 5.0]",
   "meanF[-0.0, -5.0, 5.0]", "sigmaF[2, 0.7, 15.0]",
   "alphaF[2.0, 1.2, 3.5]",
   'nF[3, -5, 5]', "sigmaF_2[2.0, 0.5, 6.0]", "sosF[1, 0.5, 5.0]",
   "tailLeft[1]",
   "RooCBExGaussShape::sigResPass(x,meanP,expr('sqrt(sigmaP*sigmaP+sosP*sosP)',{sigmaP,sosP}),alphaP,nP, expr('sqrt(sigmaP_2*sigmaP_2+sosP*sosP)',{sigmaP_2,sosP}),tailLeft)",
   "RooCBExGaussShape::sigResFail(x,meanF,expr('sqrt(sigmaF*sigmaF+sosF*sosF)',{sigmaF,sosF}),alphaF,nF, expr('sqrt(sigmaF_2*sigmaF_2+sosF*sosF)',{sigmaF_2,sosF}),tailLeft)"
 ]
  for var in tnpAltSigFit:
    w.factory(var)
  if 'AltSignal' in fitType:
    gauss_Pass = w.pdf('sigResPass')
    gauss_Fail = w.pdf('sigResFail')
  
  sig_pass = ROOT.RooFFTConvPdf("sigP", "signal shape", x, ZPassShape, gauss_Pass)
  sig_fail = ROOT.RooFFTConvPdf("sigF", "signal shape", x, ZFailShape, gauss_Fail)

  # parameter of RooCMSShape, pdf of background
  acmsP = ROOT.RooRealVar("acmsP", "acms", 60.,50.,80.)
  betaP = ROOT.RooRealVar("betaP", "beta", 0.05,0.01,0.08)
  gammaP = ROOT.RooRealVar("gammaP", "gamma", 0.1, -2, 2)
  peakP = ROOT.RooRealVar("peakP", "peak", 90.0)

  bkgP = RooCMSShape("bkgP", "bkg shape", x, acmsP, betaP, gammaP, peakP)

  acmsF = ROOT.RooRealVar("acmsF", "acms", 60.,50.,80.)
  betaF = ROOT.RooRealVar("betaF", "beta", 0.05,0.01,0.08)
  gammaF = ROOT.RooRealVar("gammaF", "gamma", 0.1, -2, 2)
  peakF = ROOT.RooRealVar("peakF", "peak", 90.0)

  bkgF = RooCMSShape("bkgF", "bkg shape", x, acmsF, betaF, gammaF, peakF)

  tnpAltBkgFit = [
    "AlphaP[0., -5., 5.]",
    "AlphaF[0., -5., 5.]",
    "Exponential::bkgP(x, AlphaP)",
    "Exponential::bkgF(x, AlphaF)",
  ]
  for var in tnpAltBkgFit:
    w.factory(var)
  if 'AltBkg' in fitType:
    bkgP = w.pdf('bkgP')
    bkgF = w.pdf('bkgF')
 
  nSigP = ROOT.RooRealVar("nSigP","nSigP",0.9*Muon_pass_total,0.5*Muon_pass_total,1.5*Muon_pass_total)
  nBkgP = ROOT.RooRealVar("nBkgP","nBkgP",0.1*Muon_pass_total,0.,1.5*Muon_pass_total)
  
  nSigF = ROOT.RooRealVar("nSigF","nSigF",0.9*Muon_fail_total,0.5*Muon_fail_total,1.5*Muon_fail_total)
  nBkgF = ROOT.RooRealVar("nBkgF","nBkgF",0.1*Muon_fail_total,0.,1.5*Muon_fail_total)
  
  modelP=ROOT.RooAddPdf("modelP","modelP", ROOT.RooArgList(sig_pass,bkgP), ROOT.RooArgList(nSigP,nBkgP))
  modelF=ROOT.RooAddPdf("modelF","modelF", ROOT.RooArgList(sig_fail,bkgF), ROOT.RooArgList(nSigF,nBkgF))
  
  Pframe = x.frame(ROOT.RooFit.Title("passing probe"))
  Fframe = x.frame(ROOT.RooFit.Title("failing probe"))
  
  if ismc:
    GenPass.plotOn(Pframe)
    rPass = sig_pass.fitTo(GenPass, ROOT.RooFit.Range("FitRange"), ROOT.RooFit.Save())
    sig_pass.plotOn(Pframe, ROOT.RooFit.LineColor(ROOT.kRed))
    GenFail.plotOn(Fframe)
    rFail = sig_fail.fitTo(GenFail, ROOT.RooFit.Range("FitRange"), ROOT.RooFit.Save())
    sig_fail.plotOn(Fframe, ROOT.RooFit.LineColor(ROOT.kRed))
    nTot=DY_pass_total+DY_fail_total
    eff=DY_pass_total/nTot
    e_eff = 1./(nTot*nTot) * sqrt( DY_pass_total*DY_pass_total* DY_fail_error*DY_fail_error + DY_fail_total*DY_fail_total * DY_pass_error*DY_pass_error )


  if not ismc:
    DataPass.plotOn(Pframe)
    rPass = modelP.fitTo(DataPass, ROOT.RooFit.Range("FitRange"), ROOT.RooFit.Save())
    modelP.plotOn(Pframe, ROOT.RooFit.LineColor(ROOT.kRed))
    modelP.plotOn(Pframe, ROOT.RooFit.Components("bkgP"),ROOT.RooFit.LineColor(ROOT.kBlue),ROOT.RooFit.LineStyle(ROOT.kDashed))
    DataFail.plotOn(Fframe)
    rFail = modelF.fitTo(DataFail, ROOT.RooFit.Range("FitRange"), ROOT.RooFit.Save())
    modelF.plotOn(Fframe, ROOT.RooFit.LineColor(ROOT.kRed))
    modelF.plotOn(Fframe, ROOT.RooFit.Components("bkgF"),ROOT.RooFit.LineColor(ROOT.kBlue),ROOT.RooFit.LineStyle(ROOT.kDashed))
    nTot=nSigP.getVal()+nSigF.getVal()
    eff=nSigP.getVal()/nTot
    e_eff = 1./(nTot*nTot)*sqrt(nSigP.getVal()*nSigP.getVal()*nSigF.getError()*nSigF.getError() + nSigF.getVal()*nSigF.getVal() * nSigP.getError()*nSigP.getError() )


  c1=TCanvas("TnP","TnP",1200,600)
  c1.Divide(3,1)
  c1.cd(2)
  Pframe.Draw()
  c1.cd(3)
  Fframe.Draw()

  # Add text results
  text1 = ROOT.TPaveText(0.05,0.75,0.3,0.95)
  text1.SetFillColor(0)
  text1.SetBorderSize(0)
  text1.SetTextAlign(12)
  if ismc:
    text1.AddText('* MC Fit status:')
    text1.AddText('passing: '+str(rPass.status())+', '+'failing: '+str(rFail.status()))
    text1.AddText('* Eff = '+str('%1.4f'%eff)+' #pm '+str('%1.4f'%e_eff))
    text1.SetTextSize(0.08)
  else:
    text1.AddText('* Data Fit status:')
    text1.AddText('passing: '+str(rPass.status())+', '+'failing: '+str(rFail.status()))
    text1.AddText('* Eff = '+str('%1.4f'%eff)+' #pm '+str('%1.4f'%e_eff))
    text1.SetTextSize(0.08)

  text2 = ROOT.TPaveText(0.05,0.05,0.3,0.72)
  text2.SetFillColor(0)
  text2.SetBorderSize(0)
  text2.SetTextAlign(12)
  if ismc:
    text2.AddText('  --- parameters ')
    text2.AddText('-meanP = '+str('%1.3f'%meanPass.getVal())+' #pm '+str('%1.3f'%meanPass.getError()))
    text2.AddText('-sigmaP = '+str('%1.3f'%sigmaPass.getVal())+' #pm '+str('%1.3f'%sigmaPass.getError()))
    text2.AddText('-nSigP = '+str('%1.3f'%DY_pass_total)+' #pm '+str('%1.3f'%DY_pass_error))
    text2.AddText('-meanF = '+str('%1.3f'%meanFail.getVal())+' #pm '+str('%1.3f'%meanFail.getError()))
    text2.AddText('-sigmaF = '+str('%1.3f'%sigmaFail.getVal())+' #pm '+str('%1.3f'%sigmaFail.getError()))
    text2.AddText('-nSigF = '+str('%1.3f'%DY_fail_total)+' #pm '+str('%1.3f'%DY_fail_error))
    text2.SetTextSize(0.06)
  else:
    text2.AddText('  --- parameters ')
    text2.AddText('-nBkgP = '+str('%1.3f'%nBkgP.getVal())+' #pm '+str('%1.3f'%nBkgP.getError()))
    text2.AddText('-nSigP = '+str('%1.3f'%nSigP.getVal())+' #pm '+str('%1.3f'%nSigP.getError()))
    text2.AddText('-meanP = '+str('%1.3f'%meanPass.getVal())+' #pm '+str('%1.3f'%meanPass.getError()))
    text2.AddText('-sigmaP = '+str('%1.3f'%sigmaPass.getVal())+' #pm '+str('%1.3f'%sigmaPass.getError()))
    text2.AddText('-acmsP = '+str('%1.3f'%acmsP.getVal())+' #pm '+str('%1.3f'%acmsP.getError()))
    text2.AddText('-betaP = '+str('%1.3f'%betaP.getVal())+' #pm '+str('%1.3f'%betaP.getError()))
    text2.AddText('-gammaP = '+str('%1.3f'%gammaP.getVal())+' #pm '+str('%1.3f'%gammaP.getError()))
    text2.AddText('-nBkgF = '+str('%1.3f'%nBkgF.getVal())+' #pm '+str('%1.3f'%nBkgF.getError()))
    text2.AddText('-nSigF = '+str('%1.3f'%nSigF.getVal())+' #pm '+str('%1.3f'%nSigF.getError()))
    text2.AddText('-meanF = '+str('%1.3f'%meanFail.getVal())+' #pm '+str('%1.3f'%meanFail.getError()))
    text2.AddText('-sigmaF = '+str('%1.3f'%sigmaFail.getVal())+' #pm '+str('%1.3f'%sigmaFail.getError()))
    text2.AddText('-acmsF = '+str('%1.3f'%acmsF.getVal())+' #pm '+str('%1.3f'%acmsF.getError()))
    text2.AddText('-betaF = '+str('%1.3f'%betaF.getVal())+' #pm '+str('%1.3f'%betaF.getError()))
    text2.AddText('-gammaF = '+str('%1.3f'%gammaF.getVal())+' #pm '+str('%1.3f'%gammaF.getError()))
    text2.SetTextSize(0.05)

  c1.cd(1)
  text1.Draw()
  text2.Draw()
  if ismc:
    c1.SaveAs(filename+"_mc.png")
  else:
    c1.SaveAs(filename+"_data.png")

  return eff, e_eff

def produce_SF(fitType,inputDir,plotDir,tag):
  tdptbin=array('d',[10,20,35,50,100,200,500])
  tdptbin_plain=array('d',[1,2,3,4,5,6,7])
  tdptbinname=['10~20','20~35','35~50','50~100','100~200','200~500']
  tdetabin=array('d',[0.0,0.8,1.4442,1.566,2.0,2.5])

  h2_SF = ROOT.TH2D('muIDSF', 'muIDSF', 6, tdptbin_plain, 5, tdetabin)
  h2_SF.Sumw2()
  h2_SF.SetStats(0)
  h2_SF.GetXaxis().SetTitle('Muon P_{T} [GeV]')
  h2_SF.GetYaxis().SetTitle('Muon #||{#eta}')
  h2_SF.SetTitle('')
  for ib in range(1,7):
    h2_SF.GetXaxis().SetBinLabel(ib,tdptbinname[ib-1])

  h2_data = ROOT.TH2D('muIdSF', 'muIdSF', 6, tdptbin, 5, tdetabin)
  h2_data.Sumw2()
  h2_data.SetStats(0)
  h2_data.GetXaxis().SetTitle('Muon P_{T} [GeV]')
  h2_data.GetYaxis().SetTitle('Muon #||{#eta}')
  h2_data.SetTitle('')

  h2_mc = ROOT.TH2D('muIDMCEff', 'muIDMCEff', 6, tdptbin, 5, tdetabin)
  h2_mc.Sumw2()
  h2_mc.SetStats(0)
  h2_mc.GetXaxis().SetTitle('Muon P_{T} [GeV]')
  h2_mc.GetYaxis().SetTitle('Muon #||{#eta}')
  h2_mc.SetTitle('')

  ptbinnames=['Pt10To20','Pt20To35','Pt35To50','Pt50To100','Pt100To200','Pt200To500']
  etabinnames=['Etam0p0Top0p8','Etap0p8Top1p4442','Etap1p4442Top1p566','Etap1p566Top2p0','Etap2p0Top2p5']

  for files in os.listdir(inputDir):
    if not (files.startswith('Pt') and files.endswith('.root')):continue

    eff,eff_err = muSF(fitType,0,inputDir+files)
    for i in range(len(ptbinnames)):
      for j in range(len(etabinnames)):
        if (ptbinnames[i] in files) and (etabinnames[j] in files):
          print(files)
          h2_data.SetBinContent(i+1,j+1,eff)
          h2_data.SetBinError(i+1,j+1,eff_err)

    eff_mc, eff_err_mc = muSF(fitType,1,inputDir+files)
    for i in range(len(ptbinnames)):
      for j in range(len(etabinnames)):
        if (ptbinnames[i] in files) and (etabinnames[j] in files):
          print(i,j,eff_mc,eff_err_mc)
          h2_mc.SetBinContent(i+1,j+1,eff_mc)
          h2_mc.SetBinError(i+1,j+1,eff_err_mc)
  print(h2_data.GetBinContent(1,1))
  h2_data.Divide(h2_mc)
  print(h2_data.GetBinContent(1,1))
  for ix in range(h2_data.GetNbinsX()):
    for iy in range(h2_data.GetNbinsY()):
      h2_SF.SetBinContent(ix+1,iy+1,h2_data.GetBinContent(ix+1,iy+1))
      h2_SF.SetBinError(ix+1,iy+1,h2_data.GetBinError(ix+1,iy+1))

  c1 = TCanvas()
  pad1 = TPad()
  pad1.Draw()
  pad1.cd()
  h2_data.Draw('COLZ TEXT E')
  CMSstyle.SetStyle(pad1)
  pad1.SetRightMargin(0.15)
  c1.SetGridx(False);
  c1.SetGridy(False);
  c1.SaveAs('%s/SF_%s.png'%(plotDir,tag))
  c1.SaveAs('%s/SF_%s.pdf'%(plotDir,tag))
  pad1.Close()

  c2 = TCanvas()
  pad2 = TPad()
  pad2.Draw()
  pad2.cd()
  h2_SF.Draw('COLZ TEXT E')
  CMSstyle.SetStyle(pad2)
  pad2.SetRightMargin(0.15)
  c2.SetGridx(False);
  c2.SetGridy(False);
  c2.SaveAs('%s/SF_plainX_%s.png'%(plotDir,tag))
  c2.SaveAs('%s/SF_plainX_%s.pdf'%(plotDir,tag))
  pad2.Close()
  return h2_data

def get_sys(h_nominal,h_sys,hname,plotDir):
  tdptbin=array('d',[10,20,35,50,100,200,500])
  tdptbin_plain=array('d',[1,2,3,4,5,6,7])
  tdptbinname=['10~20','20~35','35~50','50~100','100~200','200~500']
  tdetabin=array('d',[0.0,0.8,1.4442,1.566,2.0,2.5])

  nbinX = h_nominal.GetNbinsX()
  nbinY = h_nominal.GetNbinsY()
  h_syserr = ROOT.TH2D(hname, hname, nbinX, tdptbin, nbinY, tdetabin)
  h_syserr_plain = ROOT.TH2D(hname+"_plain", hname+"_plain", nbinX, tdptbin_plain, nbinY, tdetabin)

  h_syserr.SetStats(0)
  h_syserr.GetXaxis().SetTitle('Muon P_{T} [GeV]')
  h_syserr.GetYaxis().SetTitle('Muon #||{#eta}')
  h_syserr.SetTitle('')

  h_syserr_plain.SetStats(0)
  h_syserr_plain.GetXaxis().SetTitle('Muon P_{T} [GeV]')
  h_syserr_plain.GetYaxis().SetTitle('Muon #||{#eta}')
  h_syserr_plain.SetTitle('')
  for ib in range(1,7):
    h_syserr_plain.GetXaxis().SetBinLabel(ib,tdptbinname[ib-1])

  for i in range(nbinX):
    for j in range(nbinY):
      err = 0.
      for h in h_sys:
        print(h.GetBinContent(i+1,j+1),h_nominal.GetBinContent(i+1,j+1))
        err += abs(h.GetBinContent(i+1,j+1)-h_nominal.GetBinContent(i+1,j+1))
      err = err/float(len(h_sys))
      print(i,j,err)
      h_syserr.SetBinContent(i+1,j+1,err)
      h_syserr_plain.SetBinContent(i+1,j+1,err)

  c1 = TCanvas()
  pad1 = TPad()
  pad1.Draw()
  pad1.cd()
  h_syserr.Draw('COLZ TEXT')
  CMSstyle.SetStyle(pad1)
  pad1.SetRightMargin(0.15)
  c1.SetGridx(False);
  c1.SetGridy(False);
  c1.SaveAs('%s/sys_%s.png'%(plotDir,hname))
  c1.SaveAs('%s/sys_%s.pdf'%(plotDir,hname))
  pad1.Close()

  c2 = TCanvas()
  pad2 = TPad()
  pad2.Draw()
  pad2.cd()
  h_syserr_plain.Draw('COLZ TEXT')
  CMSstyle.SetStyle(pad2)
  pad2.SetRightMargin(0.15)
  c2.SetGridx(False);
  c2.SetGridy(False);
  c2.SaveAs('%s/sys_plainX_%s.png'%(plotDir,hname))
  c2.SaveAs('%s/sys_plainX_%s.pdf'%(plotDir,hname))
  pad2.Close()

  return h_syserr

if __name__ == "__main__":
  ntupleDir = "/afs/cern.ch/user/t/tihsu/ExYukawa/CMSSW_10_6_16/src/MuonIDSclaeFactor/flatten/"
  plotDir = "plot"
  eras = ["apv2016","2016","2017","2018"]
  for era in eras:
    #h_here = produce_SF(["Nominal"],"./","./","here")
    h_nominal = produce_SF(["Nominal"],ntupleDir+"/%s/puWeight/LO/"%era,plotDir,"nominal_%s"%era)
    h_puUp    = produce_SF(["Nominal"],ntupleDir+"/%s/puWeightUp/LO/"%era,plotDir,"puUp_%s"%era)
    h_puDown  = produce_SF(["Nominal"],ntupleDir+"/%s/puWeightDown/LO/"%era,plotDir,"puDown_%s"%era)
    h_AltSig  = produce_SF(["AltSignal"],ntupleDir+"/%s/puWeight/LO/"%era,plotDir,"AltSignal_%s"%era)
    h_AltBkg  = produce_SF(["AltBkg"],ntupleDir+"/%s/puWeight/LO/"%era,plotDir,"AltBkg_%s"%era)
    h_NLO     = produce_SF(["Nominal"],ntupleDir+"/%s/puWeight/NLO/"%era,plotDir,"NLO_%s"%era)
    h_pu_sys     = get_sys(h_nominal,[h_puUp,h_puDown],"pu_%s"%era,plotDir)
    h_AltSig_sys = get_sys(h_nominal,[h_AltSig],"AltSig_%s"%era,plotDir)
    h_AltBkg_sys = get_sys(h_nominal,[h_AltBkg],"AltBkg_%s"%era,plotDir)
    h_NLO_sys    = get_sys(h_nominal,[h_NLO],"NLO_%s"%era,plotDir)

    h_sys = [h_pu_sys, h_AltSig_sys, h_AltBkg_sys, h_NLO_sys]
    tdptbin=array('d',[10,20,35,50,100,200,500])
    tdptbin_plain=array('d',[1,2,3,4,5,6,7])
    tdptbinname=['10~20','20~35','35~50','50~100','100~200','200~500']
    tdetabin=array('d',[0.0,0.8,1.4442,1.566,2.0,2.5])

    nbinX = h_nominal.GetNbinsX()
    nbinY = h_nominal.GetNbinsY()

    h_sys_combine = ROOT.TH2D('sys_error', 'sys_error', nbinX, tdptbin, nbinY, tdetabin)
    h_sys_combine_plain = ROOT.TH2D("sys_error_plain", "sys_error_plain", nbinX, tdptbin_plain, nbinY, tdetabin)
    h_err_combine = ROOT.TH2D("combined_error","combined_error", nbinX, tdptbin, nbinY, tdetabin)
    h_err_combine_plain = ROOT.TH2D("combined_error_plain", "combined_error_plain", nbinX, tdptbin_plain, nbinY, tdetabin)

    h_sys_combine.SetStats(0)
    h_sys_combine.GetXaxis().SetTitle('Muon P_{T} [GeV]')
    h_sys_combine.GetYaxis().SetTitle('Muon #||{#eta}')
    h_sys_combine.SetTitle('')

    h_sys_combine_plain.SetStats(0)
    h_sys_combine_plain.GetXaxis().SetTitle('Muon P_{T} [GeV]')
    h_sys_combine_plain.GetYaxis().SetTitle('Muon #||{#eta}')
    h_sys_combine_plain.SetTitle('')
    for ib in range(1,7):
      h_sys_combine_plain.GetXaxis().SetBinLabel(ib,tdptbinname[ib-1])
      h_err_combine_plain.GetXaxis().SetBinLabel(ib,tdptbinname[ib-1])

    h_err_combine.SetStats(0)
    h_err_combine.GetXaxis().SetTitle('Muon P_{T} [GeV]')
    h_err_combine.GetYaxis().SetTitle('Muon #||{#eta}')
    h_err_combine.SetTitle('')

    h_err_combine_plain.SetStats(0)
    h_err_combine_plain.GetXaxis().SetTitle('Muon P_{T} [GeV]')
    h_err_combine_plain.GetYaxis().SetTitle('Muon #||{#eta}')
    h_err_combine_plain.SetTitle('')

    for i in range(nbinX):
      for j in range(nbinY):
        err_sys = 0.
        err_stat = 0.
        for h in h_sys:
          err_sys += (h.GetBinContent(i+1,j+1))**2
        err_sys = sqrt(err_sys)
        err_stat = h_nominal.GetBinError(i+1,j+1)
        h_sys_combine.SetBinContent(i+1,j+1,err_sys)
        h_sys_combine_plain.SetBinContent(i+1,j+1,err_sys)
        h_err_combine.SetBinContent(i+1,j+1,sqrt(err_sys**2+err_stat**2))
        h_err_combine_plain.SetBinContent(i+1,j+1,sqrt(err_sys**2+err_stat**2))

    c1 = TCanvas()
    pad1 = TPad()
    pad1.Draw()
    pad1.cd()
    h_sys_combine.Draw('COLZ TEXT E')
    CMSstyle.SetStyle(pad1)
    pad1.SetRightMargin(0.15)
    c1.SetGridx(False);
    c1.SetGridy(False);
    c1.SaveAs('%s/sys_combine_%s.png'%(plotDir,era))
    c1.SaveAs('%s/sys_combine_%s.pdf'%(plotDir,era))
    h_err_combine.Draw('COLZ TEXT E')
    c1.SetGridx(False);
    c1.SetGridy(False);
    c1.SaveAs('%s/err_combine_%s.png'%(plotDir,era))
    c1.SaveAs('%s/err_combine_%s.pdf'%(plotDir,era))
    pad1.Close()

    c2 = TCanvas()
    pad2 = TPad()
    pad2.Draw()
    pad2.cd()
    h_sys_combine_plain.Draw('COLZ TEXT E')
    CMSstyle.SetStyle(pad2)
    pad2.SetRightMargin(0.15)
    c2.SetGridx(False);
    c2.SetGridy(False);
    c2.SaveAs('%s/sys_combine_plainX_%s.png'%(plotDir,era))
    c2.SaveAs('%s/sys_combine_plainX_%s.pdf'%(plotDir,era))
    h_err_combine_plain.Draw('COLZ TEXT E')
    c2.SetGridx(False);
    c2.SetGridy(False);
    c2.SaveAs('%s/err_combine_plainX_%s.png'%(plotDir,era))
    c2.SaveAs('%s/err_combine_plainX_%s.pdf'%(plotDir,era))
    pad2.Close()

    fout = ROOT.TFile('muonIdSF_%sUL.root'%era,'recreate')
    fout.cd()

    h_nominal.Write()
    for h in h_sys:
      h.Write()
    h_sys_combine.Write()
    h_err_combine.Write()
    fout.Close()
